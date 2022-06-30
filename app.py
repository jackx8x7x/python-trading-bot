import sys
import time
import json
import asyncio
import logging
import curses
import numpy as np
import argparse
from datetime import datetime
from datetime import timezone
from datetime import timedelta
from lib.tradding import Trader
from lib.transactions import Transactions

'''
	'LTC_USD', 'BCO_USD', 'XAG_USD', 'BTC_USD', 'XAU_USD', 'CORN_USD',
	'TWIX_USD', 'CAD_JPY', 'CN50_USD', 'USD_CAD', 'USD_JPY', 'USD_CHF',
	'UK100_GBP', 'CHF_ZAR', 'WTICO_USD', 'GBP_USD', 'WHEAT_USD', 'EUR_USD',
	'CHF_JPY', 'USB10Y_USD', 'SOYBN_USD', 'EUR_JPY', 'DE30_EUR', 'SPX500_USD',
	'NAS100_USD', 'NATGAS_USD', 'DE10YB_EUR', 'SUGAR_USD', 'AUD_JPY',
	'US30_USD', 'AUD_USD', 'XCU_USD']
'''

instruments = [
	'BCO_USD', 'XAU_USD', 'USD_CAD', 'USD_JPY', 'USD_CHF', 'UK100_GBP',
	'WTICO_USD', 'GBP_USD', 'EUR_USD', 'DE30_EUR',
	'SPX500_USD', 'NAS100_USD', 'US30_USD', 'AUD_USD'
]

OpenPositionFields = ("Instrument", "Units", "UnrealizedPL", "AveragePrice", "Change")
class App:
	def __init__(self, stdscr, trader):
		self.stdscr = stdscr
		self.stdscr.nodelay(True)
		self.trader = trader
		self.interval = 1
		self.sortBy = 'instrument'
		lines, cols = curses.LINES, curses.COLS
		assert lines >= 24
		assert cols >= 80
	
		curses.start_color()
		curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
		curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_RED)
	
		half = int(lines/2)
	
		# windows for tracing open/instrument positions and account state
		self.accountWin = curses.newwin(3, cols, 0, 0)
		self.reportWin = curses.newwin(lines - half + 3, 52*3, 3, 0)
		self.openPosWin = curses.newwin(lines - half, 68, lines-half + 6, 0)
		self.lastPL = curses.newwin(lines - half, 40, lines-half + 6, 68)
		self.lastOrder = curses.newwin(lines - half, cols - 108, lines-half + 6, 108)

	async def inputHandler(self):
		# hours rotate when user pres blank
		intervals = [1, 2, 6, 12, 24, 72, 168, 24*30, 24*365]
		sorts = ['instrument', 'ord', 'PL', 'rate']
		l, ls = len(intervals), len(sorts)
		i, j = 0, 0
		while True:
			try:
				k = self.stdscr.getkey()
			except:
				await asyncio.sleep(0.01)
				continue

			if k == ' ' or k == curses.KEY_DOWN or k == 'j':
				i = (i+1) % l
				self.interval = intervals[i]
			elif k == curses.KEY_UP or k == 'k':
				i = (i-1) % l
				self.interval = intervals[i]
			elif k == 's':
				j = (j+1) % ls
				self.sortBy = sorts[j]
			elif k in ['d', 'w']:
				self.interval = 24 if k == 'd' else 168

	async def openPositionsStateUI(self):
		trader = self.trader
		stdscr = self.openPosWin
		fieldWidth = max(
			map(lambda x: len(x), OpenPositionFields)
		) + 1
		fieldBar = "".join(("%*s" % (fieldWidth, _) for _ in OpenPositionFields))
	
		while True:
			await asyncio.sleep(0.1)
			y, x = stdscr.getmaxyx()
	
			stdscr.erase()
			stdscr.addstr(1, 1, fieldBar,
				curses.A_STANDOUT)
			stdscr.border()
	
			i = 2
			for name, instr in trader.instruments.items():
				op = instr.openPositions
				if op:
					pl = op.get('unrealizedPL')
					for side in ['long', 'short']:
						pos = op[side]
						if not float(pos['units']):
							continue

						if i > y - 2:
							break

						price = float(pos.get('averagePrice'))
							
						_ = (instr.lastPrice - price)*100/price
						if side == 'short':
							_ = -_
						change = "%.2f%%" % _

						s = ''.join(( "%*s" % (fieldWidth, _) for _ in (
									name,
									pos.get('units'),
									pl,
									pos.get('averagePrice'),
									change
								)))
						if float(pl) < 0:
							stdscr.attron(curses.color_pair(2))
						stdscr.addstr(i, 1, s)
						if float(pl) < 0:
							stdscr.attroff(curses.color_pair(2))
						i = i+1
	
			stdscr.refresh()
	
	async def accountStateUI(self):
		trader = self.trader
		stdscr = self.accountWin

		while True:
			stdscr.erase()
			stdscr.border()
	
	#		stdscr.attron(curses.color_pair(1))
			ac = trader.accountState
			marginU = int(ac.marginUsed*100/ac.NAV)
	
			stdscr.addstr(1, 1,
			"%s  %s  NAV: %6.2f  Open: %3u  Used: %.2f(%2u%%)  Unrealized: %s  P/L: %s"
			% (datetime.now(tz=timezone.utc).ctime(), ac.alias, ac.NAV, ac.openPositionCount,
			ac.marginUsed, marginU, ac.unrealizedPL, ac.pl)
			)
			stdscr.attroff(curses.A_STANDOUT)
	
			stdscr.refresh()
			await asyncio.sleep(0.1)
	
	'''
	Window show intrument's trading performance by showing realized P/L
	'''
	async def updateUI(self):
		while True:
			t = asyncio.create_task(self.updateLastPL())
			t0 = asyncio.create_task(self.updateLastOrder())
			t1 = asyncio.create_task(self.updateReport())
			await t
			await t0
			await t1
			await asyncio.sleep(0.5)

	async def updateReport(self):
		trader = self.trader
		stdscr = self.reportWin
		transactions = trader.transactions
		y, x = stdscr.getmaxyx()
		interval = self.interval
		showInterval = {
			1: '1 hr',
			2: '2 hrs',
			6: '6 hrs',
			12: '12 hrs',
			24: '1 Day',
			72: '3 days',
			168: '1 Week',
			24*30: '30 days',
			24*365: '1 year'
		}[interval]

		stdscr.erase()
		stdscr.border()
		titles = [
			"All trade in last %s" % showInterval,
			"Profit in last %s" % showInterval,
			"Loss in last %s" % showInterval
		]
		for i in range(3):
			title = titles[i]
			stdscr.addstr(1, 1+52*i, "   %-47s" % title, curses.A_STANDOUT)
			s = " %6s %12s %8s %9s %10s" % ('Item',
				'Instrument','Orders', 'P/L', 'pl/orders')
			stdscr.addstr(2, 1+52*i, s, curses.A_STANDOUT)

		modes = ['!=', '>', '<']
		for j in range(3):
			order = 0
			pl = 0
			mode = modes[j]
			trans = await transactions.getReport(hrs = interval, mode=mode,
			sort=self.sortBy)
			i = 3
			for t in trans:
				s = " %6u %12s %8u %9.2f %10.2f" % (i-2, *t)
				order = order + t[1]
				pl = pl + t[2]
				if i < y-2:
					if t[2] < 0:
						stdscr.attron(curses.color_pair(2))
					stdscr.addstr(i, 1+j*52, s)
					if t[2] < 0:
						stdscr.attroff(curses.color_pair(2))
					i = i+1

			rate = pl/order if order else 0
			s = " %6s %12s %8u %9.2f %10.2f" % ('Total', '', order, pl, rate)
			stdscr.attron(curses.color_pair(1))
			stdscr.addstr(y-2, 1+j*52, s)
			stdscr.attroff(curses.color_pair(1))
		stdscr.refresh()

	async def updateLastPL(self):
		trader = self.trader
		stdscr = self.lastPL
		transactions = trader.transactions
		stdscr.erase()
		stdscr.border()
		y, x = stdscr.getmaxyx()
		s = "%9s %10s %10s %6s" % ('Datetime', 'Instrument', 'Units', 'P/L')
		stdscr.addstr(1, 1, s, curses.A_STANDOUT)
		num = y-3
		li = transactions.getLastPL(num=num)
		i = 0
		for r in li:
			s = "%9s %10s %10.1f %6.2f" % r
			stdscr.addstr(2+i, 1, s)
			i = i+1
		stdscr.refresh()

	async def updateLastOrder(self):
		trader = self.trader
		stdscr = self.lastOrder
		transactions = trader.transactions
		stdscr.erase()
		stdscr.border()
		y, x = stdscr.getmaxyx()
		s = "%9s %10s %10s" % ('Datetime', 'Instrument', 'Units')
		stdscr.addstr(1, 1, s, curses.A_STANDOUT)
		num = y-3
		li = transactions.getLastOrder(num=num)
		i = 0
		for r in li:
			s = "%9s %10s %10.1f" % r
			stdscr.addstr(2+i, 1, s)
			i = i+1
		stdscr.refresh()
	
	async def run(self):
		accountStateTracing = asyncio.create_task(self.accountStateUI())
		openPositionsTracing = asyncio.create_task(self.openPositionsStateUI())
		updateUI = asyncio.create_task(self.updateUI())
		inputHandler = asyncio.create_task(self.inputHandler())
		await self.trader.run()

'''
Use for combine asyncio and curses.wrapper
'''
def main(stdscr, trader):
	app = App(stdscr, trader)
	asyncio.run(app.run())

debugMode = 0
textUi = 0

logger = logging.getLogger(__name__)
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Oanda v20 API trader')
	parser.add_argument('-d', '--debug', action='store_true',
		help='Run in the debug mode')
	parser.add_argument('-D', '--demo', action='store_true',
		help='Run in the demo mode')
	parser.add_argument('-t', '--textui', action='store_true',
		help='Run in the text-ui mode')
	parser.add_argument('-l', '--log', metavar='LOGFILE',
		help='Log into file LOGFILE')
	parser.add_argument('-r', '--report', action='store_true',
		help='Run in the report only mode and not to trade')

	args = parser.parse_args()

	with open('app.conf', 'r') as f:
		config = json.load(f)
	
	demoMode = config.get('DEMO', 0)
	debugMode = config.get('DEBUG', 0)
	textUi = config.get('TEXTUI', 0)
	logfile = config.get('logfile', 'trader.log')

	if args.report:
		config['reportOnly'] = True
	if args.debug:
		debugMode = 1
		config['DEBUG'] = 1
	if args.demo:
		demoMode = 1
		config['DEMO'] = 1
		config['sqlite'] = 'demo-transactions.db'
		logfile = 'demo-trader.log'
		config['logfile'] = 'demo-trader.log'
	if args.textui:
		textUi = 1
		config['TEXTUI'] = 1
	if args.log:
		logfile = args.log
		config['logfile'] = args.log

	instruments = []
	with open('instruments.conf', 'r') as f:
		_ = json.load(f)
		instruments = _.get('instruments', [])

	t = Trader(config, instruments)

	level = logging.DEBUG if debugMode == 1 else logging.INFO

	if textUi == 1:
		logging.basicConfig(filename=logfile, level=level)
		logger.info(f"start at {datetime.now(tz=timezone.utc).ctime()}")
		curses.wrapper(main, t)
	else:
		logging.basicConfig(level=level)
		logger.info(f"start at {datetime.now(tz=timezone.utc).ctime()}")
		asyncio.run(t.run())

