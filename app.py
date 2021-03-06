import json
import asyncio
import logging
import curses
import argparse
from datetime import datetime
from datetime import timezone
from lib.trader import Trader
from lib.interface import Dashboard

'''
Use for combine asyncio and curses.wrapper
'''
def main(stdscr, trader):
	dashboard = Dashboard(stdscr, trader)
	asyncio.run(dashboard.run())

logger = logging.getLogger(__name__)
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='A trading-bot using OANDA v20 API')
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

	with open('conf/app.conf', 'r') as f:
		config = json.load(f)
	
	'''
	Configuration order: command line options then app.conf
	'''
	debugMode = config.get('DEBUG', 0)
	textUi = config.get('TEXTUI', 0)
	logfile = config.get('logfile', 'log/trader.log')

	if args.report:
		config['reportOnly'] = True
	if args.debug:
		debugMode = 1
		config['DEBUG'] = 1
	if args.demo:
		config['DEMO'] = 1
	if args.textui:
		textUi = 1
		config['TEXTUI'] = 1
	if args.log: # overwrite setting above
		logfile = args.log

	level = logging.DEBUG if debugMode == 1 else logging.INFO

	t = Trader(config)


	# Use curses text-based UI
	if textUi == 1:
		logging.basicConfig(filename=logfile, level=level)
		logger.info(f"start at {datetime.now(tz=timezone.utc).ctime()}")
		curses.wrapper(main, t)
	else:
		logging.basicConfig(level=level)
		logger.info(f"start at {datetime.now(tz=timezone.utc).ctime()}")
		asyncio.run(t.run())

