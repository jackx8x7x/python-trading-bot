import json
import asyncio
import logging
import sqlite3
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from lib.api import ApiWrapper

logger = logging.getLogger(__name__)

'''
class logs trade history to create report
'''
class Transactions(ApiWrapper):
	def __init__(self, config: dict):
		super().__init__(config)
		self.db = config.get("dbname", "order_fill")
		self.sqlite = config.get("sqlite", "transactions.db")
		self.initdb()
		self.tz = timezone.utc
	
	def now(self):
		return datetime.now(tz=self.tz)

	def initdb(self):
		with sqlite3.connect(self.sqlite) as con:
			cur = con.cursor()
			cur.execute(f'''
				CREATE TABLE IF NOT EXISTS {self.db} (
					id INTEGER PRIMARY KEY,
					time INTEGER,
					instrument TEXT,
					units REAL,
					pl REAL,
					accountBalance REAL,
					reason TEXT
				);
			''')
	
	def insertBulk(self, bulk: list):
		with sqlite3.connect(self.sqlite) as con:
			cur = con.cursor()
			for d in bulk:
				ID = d.get('id')
				time = d.get('time')
				instru = d.get('instrument')
				units = d.get('units')
				pl = d.get('pl')
				accountBalance = d.get('accountBalance')
				reason = d.get('reason')
				try:
					cur.execute('''
						INSERT INTO order_fill
						VALUES (
							?,?,?,?,?,?,?
						);
					''', (ID, time, instru, units, pl, accountBalance, reason)
					)
				except:
					pass
	
	async def getLastID(self):
		_ = await self.getAccountSummary()
		self.lastID = _.get('lastTransactionID')
		if not self.lastID:
			logger.info('No last transaction ID return')
		return self.lastID

	async def retrieveAll(self):
		await self.getLastID()
		if not self.lastID:
			logger.info('No last transaction ID')
			return

		with sqlite3.connect(self.sqlite) as con:
			cur = con.cursor()
			cur.execute('SELECT max(id) from order_fill;')
			lastID = cur.fetchone()[0] # max id in database
		if not lastID:
			lastID = 0

		step = 500
		for i in range(lastID, int(self.lastID), step):
			trans = await self.getTransactions(sinceID=i, toID=i+500, t='ORDER_FILL')
			self.insertBulk(trans)
	
	# Mode is !=, > or <
	async def getReport(self, hrs=1, mode='!=', sort='instrument'):
		hrs = int(hrs)
		since = self.now() - timedelta(hours=hrs)
		return await self.reportInRange(since=since, mode=mode, sort=sort)

	'''
	Generate report for each instrument on a give time range
	Number of
		order create
		pl > 0 / pl < 0
		stoploss/takeprofit/close order
	time range
		1 hr/today/lastday/1 week
	'''
	async def reportInRange(self, since: datetime,
	to=None, mode='!=', sort='instrument'):
		assert mode in ['!=', '<', '>']
		assert sort in ['instrument', 'ord', 'PL', 'rate']
		await self.retrieveAll()

		sinceUnix = since.strftime("%s")
		if not to:
			toUnix = datetime.now(tz=timezone.utc).strftime("%s")
		else:
			toUnix = to.strftime("%s")
		logger.debug(f"since: {since} {sinceUnix}")
		logger.debug(f"to: {to} {toUnix}")

		with sqlite3.connect(self.sqlite) as con:
			cur = con.cursor()
			sql = f'''
			SELECT i, c, s FROM
				(SELECT instrument as i, count(id) as c, sum(pl) as s
				FROM {self.db}
				WHERE pl > 0 and time > {sinceUnix} and time < {toUnix}
				GROUP BY instrument
			UNION
				SELECT instrument as i, count(id) as c, sum(pl) as s
				FROM {self.db}
				WHERE pl < 0 and time > {sinceUnix} and time < {toUnix}
				GROUP BY instrument)
			ORDER BY s DESC
			'''

			sql = f'''
			SELECT instrument, ord, PL, PL/ord as rate FROM
			(SELECT instrument, count(id) as ord, sum(pl) as PL
			FROM {self.db}
			WHERE pl {mode} 0 and time > {sinceUnix} and time < {toUnix}
			GROUP BY instrument)
			ORDER BY {sort} DESC'''

			rec = cur.execute(sql)
			return rec

	def getLastPL(self, num):
		with sqlite3.connect(self.sqlite) as con:
			cur = con.cursor()
			sql = f'''
			SELECT time(time, 'unixepoch'), instrument, units, pl
			FROM order_fill
			WHERE pl != 0
			ORDER BY id DESC LIMIT {num};'''
			rec = cur.execute(sql)
			return rec

	def getLastOrder(self, num):
		with sqlite3.connect(self.sqlite) as con:
			cur = con.cursor()
			sql = f'''
			SELECT time(time, 'unixepoch'), instrument, units
			FROM order_fill
			WHERE reason = 'MARKET_ORDER'
			ORDER BY id DESC LIMIT {num};'''
			rec = cur.execute(sql)
			return rec
