import sys
import requests
import json
import asyncio
import numpy as np
import curses
import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from .ApiWrapper import ApiWrapper
from .instrument import Instrument
from .transactions import Transactions

logger = logging.getLogger(__name__)

'''
Account summary
{
	"guaranteedStopLossOrderMode": "ALLOWED",
	"hedgingEnabled": true,
	"id": "101-011-5173002-002",
	"createdTime": "1655387226.595265979",
	"currency": "USD",
	"createdByUserID": 5173002,
	"alias": "practice robot",
	"marginRate": "0.05",
	"lastTransactionID": "7",
	"balance": "1000.0000",
	"openTradeCount": 2,
	"openPositionCount": 2,
	"pendingOrderCount": 0,
	"pl": "0.0000",
	"resettablePL": "0.0000",
	"resettablePLTime": "0",
	"financing": "0.0000",
	"commission": "0.0000",
	"dividendAdjustment": "0",
	"guaranteedExecutionFees": "0.0000",
	"unrealizedPL": "0.9687",
	"NAV": "1000.9687",
	"marginUsed": "7.0514",
	"marginAvailable": "993.9221",
	"positionValue": "141.0284",
	"marginCloseoutUnrealizedPL": "0.9826",
	"marginCloseoutNAV": "1000.9826",
	"marginCloseoutMarginUsed": "7.0514",
	"marginCloseoutPositionValue": "141.0284",
	"marginCloseoutPercent": "0.00352",
	"withdrawalLimit": "993.9221",
	"marginCallMarginUsed": "7.0514",
	"marginCallPercent": "0.00704"
}
'''
class AccountState(object):
	def __init__(self):
		self.alias = 'N/A'
		self.NAV = 1000
		self.marginUsed = 0
		self.openPositionCount = 0
		self.unrealizedPL = 0
		self.pl = 0

	def update(self, data):
		self.__dict__.update(data)
		self.NAV = float(self.NAV)
		self.marginUsed = float(self.marginUsed)
		self.unrealizedPL = float(self.unrealizedPL)
		self.pl = float(self.pl)

from os.path import dirname, join
class Trader(ApiWrapper):
	def __init__(self, config: dict):
		super().__init__(config)
		self.allowOpsCount = config.get('maxOpenPositions', 15)
		self.leverage = config.get('leverage', 20)
		self.allowMarginUsed = 0.9
		self.pollDelay = 3
		self.accountState = AccountState()
		self.transactions = Transactions(config)
		self.reportOnly = config.get('reportOnly', False)

		self.instruments = {}
		_instrConfig = 'conf/instruments.conf'
		with open(_instrConfig, 'r') as f:
			_ = json.load(f)
			instruConfig = _.get('instruments', {})
			for instrConf in instruConfig:
				instr = Instrument(config, instrConf, self)
				if instr.tradable == 1:
					self.instruments.update(
						{instr.name: instr})

	'''
	Load user-defined strategies
	'''
	def loadStrategies(self):
		pass

	'''
	Update account's state
	'''
	async def updateAccountState(self):
		_ = await self.getAccountSummary()
		if not _:
			logger.info('Get account summary fail')
			return {}

		accountState = _['account']
		self.accountState.update(accountState)

		return _

	'''
	Update each instrument's open positions state
	'''
	async def updateOpenPositions(self):
		for name, instr in self.instruments.items():
			instr.openPositions = {}

		ops = await self.getOpenPositions()
		for op in ops:
			name = op['instrument']
			if name in self.instruments:
				instr = self.instruments[name]
				instr.openPositions.update(op)

	'''
	Update account state, open positions and trading history repeatly
	'''
	async def updateState(self):
		while True:
			await self.updateAccountState()
			await self.updateOpenPositions()
			await self.transactions.retrieveAll()
			await asyncio.sleep(self.pollDelay)

	async def trade(self):
		_ = await self.updateAccountState()
		if not _:
			logger.info('Exist')
			sys.exit(-1)

		for name, instr in self.instruments.items():
			asyncio.create_task(instr.asyncTrade())

	async def run(self):
		self.updateStateTask = asyncio.create_task(self.updateState())
		if not self.reportOnly:
			self.tradeTask = asyncio.create_task(self.trade())
		await self.updateStateTask

	def now(self):
		return datetime.now(tz=timezone.utc)

