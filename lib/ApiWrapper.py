import requests
import json
import logging
from lib.api import account, transaction, position, order, instrument
from datetime import datetime
from datetime import timedelta
from datetime import timezone

class ApiWrapper:
	def __init__(self, config: dict):
		demo = config.get('DEMO', 1)
		if demo == 1:
			self.url = config.get('practice-url')
			self.accountID = config.get('practice-accountID')
			self.token = config.get('practice-token')
		else:
			self.url = config.get('url')
			self.accountID = config.get('accountID')
			self.token = config.get('token')
		self.session = requests.Session()
		self.logger = logging.getLogger(__name__)

		headers = {
			'Authorization': f'Bearer {self.token}',
			'Content-Type': 'application/json',
			'Accept-Datetime-Format': 'UNIX'
		}
		self.session.headers.update(headers)
	
	async def getAccountSummary(self) -> dict:
		return await account.getSummary(self)

	async def getInstrumentPosition(self, name: str) -> dict:
		return await position.getInstrumentPosition(self, name)

	async def getOpenPositions(self) -> list:
		return await position.getOpenPositions(self)

	async def getAllPositions(self) -> list:
		return await positoin.getAllPositions(self)

	async def closePosition(self, name: str, units) -> dict:
		return await position.closePosition(self, name, units)

	async def getTransactions(self, sinceID, toID,
	t='ORDER_FILL,CLOSE,TAKE_PROFIT_ORDER,STOP_LOSS_ORDER') -> list:
		return await transaction.getTransactionsInIdRange(self, sinceID, toID, t)

	async def createMarketOrder(self, name: str, units: str, take: str, stoploss: str):
		return await order.createMarketOrder(self, name, units, take, stoploss)

	async def getCandles(self, name, since, gran='M1'):
		return await instrument.getCandles(self, name, since, gran)

	def log(self, msg):
		time = datetime.now(tz=timezone.utc)
		timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
		self.logger.info(f'{timestamp} {msg}')

