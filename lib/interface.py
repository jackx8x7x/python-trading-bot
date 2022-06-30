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

class Dashboard:
	def __init__(self, stdscr, trader):
		self.stdscr = stdscr
		self.stdscr.nodelay(True)
		self.trader = trader
		self.interval = 1
		self.sortBy = 'PL'
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
			elif k in ['h', 'd', 'w']:
				if k == 'h':
					self.interval = 1
				elif k == 'd':
					self.interval = 24
				elif k == 'w':
					self.interval = 168
				i = intervals.index(self.interval)
			elif k == 'K':
				for _, instr in self.trader.instruments.items():
					asyncio.create_task(instr.closeLong())
					asyncio.create_task(instr.closeShort())

	async def openPositionsStateUI(self):
		OpenPositionFields = ("Instrument", "Units", "UnrealizedPL", "AveragePrice", "Change")
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
