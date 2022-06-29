import sys
import requests
import json
import asyncio
import logging
import numpy as np
from urllib.parse import urlencode
from datetime import datetime
from datetime import timedelta
from datetime import timezone

endpoints = {
	'getTransactions': 'v3/accounts/{accountID}/transactions/idrange',
	'instrumentPositions': 'v3/accounts/{accountID}/positions/{instrument}',
	'openPositions': 'v3/accounts/{accountID}/openPositions',
	'allPositions': 'v3/accounts/{accountID}/positions',
	'closePosition': 'v3/accounts/{accountID}/positions/{instrument}/close',
	'accountSummary': 'v3/accounts/{accountID}/summary',
	'candles': 'v3/instruments/{instrument}/candles',
	'order': 'v3/accounts/{accountID}/orders'
}

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
	
	'''
	Create a market order for specified instrument, units, takeprofit and
	stoploss in distance
	'''
	async def createMarketOrder(self, instr: str, units: str, take: str,
	stoploss: str):
		_ = endpoints.get('order').format(accountID = self.accountID)
		url = self.url.format(endpoint = _)

		if float(units) == 0 or float(take) == 0 or float(stoploss) == 0:
			return {}

		_ = {
			'order': {
				'type': 'MARKET',
				'instrument': instr,
				'units': str(units),
				"timeInForce": "FOK",
				'takeProfitOnFill': {
					'distance': str(take)
				},
				'stopLossOnFill': {
					'distance': str(stoploss)
				}
			}
		}
		data = json.dumps(_)
		res = self.session.post(url, data=data)
		if res.status_code == 201:
			_ = json.loads(res.text)
			return _
		else:
			self.logger.debug(f"Create order fail {res.text}")
			return {}

	def log(self, msg):
		time = datetime.now(tz=timezone.utc)
		timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
		self.logger.info(f'{timestamp} {msg}')

	def request(self, url):
		pass
	
	async def getAccountSummary(self) -> dict:
		_ = endpoints.get('accountSummary').format(accountID = self.accountID)
		url = self.url.format(endpoint = _)

		res = self.session.get(url)
		if res.status_code == 200:
			_ = json.loads(res.text)
			return _
		else:
			self.logger.info('Get account summary fail')
			self.logger.info(res.text)
			return {}

	'''
	Open position specification:
	[{
		"instrument": "USD_JPY",
		"unrealizedPL": "-0.0015",
		"marginUsed": "12.0879",
		"long": {
			...
		},
		"short": {
			"units": "-363",
			"averagePrice": "134.293"
			"tradeIDs": [
				"43642",
				"43645"
			],
			...
		},
		...
	}, ...]
	'''
	async def getInstrumentPosition(self, instr: str) -> dict:
		_ = endpoints.get('openPositions').format(accountID = self.accountID, instrument = instr)
		url = self.url.format(endpoint = _)

		res = self.session.get(url)
		if res.status_code == 200:
			_ = json.loads(res.text)
			position = _.get('position', {})
			return position
		else:
			self.logger.debug(f"getInstrumentPosition get response with code {res.status_code}")
			self.logger.debug(res.text)
			return []

	async def closePosition(self, instr: str, units) -> dict:
		_ = endpoints.get('closePosition').format(accountID = self.accountID, instrument = instr)
		url = self.url.format(endpoint = _)
		if float(units) < 0:
			data = {"shortUnits": str(-float(units))}
		else:
			data = {"longUnits": units}

		data = json.dumps(data)
		res = self.session.put(url, data=data)
		if res.status_code == 200:
			self.log(f"Close position {units} {instr}")
			_ = json.loads(res.text)
			return _
		else:
			self.log(f"Close position {units} {instr} fail")
			self.log(res.text)
			self.log(data)
			return None

	async def getOpenPositions(self) -> list:
		_ = endpoints.get('openPositions').format(accountID = self.accountID)
		url = self.url.format(endpoint = _)

		res = self.session.get(url)
		if res.status_code == 200:
			_ = json.loads(res.text)
			ops = _.get('positions', [])
			return ops
		else:
			self.logger.debug(f"getOpenPositions get response with code {res.status_code}")
			self.logger.debug(res.text)
			return []

	'''
	Get all P/L related transactions since a sinceid
	'''
	async def getTransactions(self, sinceID, toID,
	t='ORDER_FILL,CLOSE,TAKE_PROFIT_ORDER,STOP_LOSS_ORDER') -> list:
		sinceID = str(sinceID)
		toID = str(toID)
		_ = {
			'from': sinceID,
			'to': toID,
			'type':t 
		}
		query = urlencode(_)
		_ = endpoints.get('getTransactions').format(accountID = self.accountID)
		url = self.url.format(endpoint = _) + f'?{query}'

		res = self.session.get(url)
		if res.status_code == 200:
			_ = json.loads(res.text)
			ops = _.get('transactions', [])
			return ops
		else:
			self.logger.debug(f"getTransactions get response with code {res.status_code}")
			self.logger.debug(res.text)
			return []

	'''
	Get all history positions
	'''
	async def getAllPositions(self) -> list:
		_ = endpoints.get('allPositions').format(accountID = self.accountID)
		url = self.url.format(endpoint = _)

		res = self.session.get(url)
		if res.status_code == 200:
			_ = json.loads(res.text)
			positions = _.get('positions', [])
			return positions
		else:
			self.logger.debug(f"getAllPositions get response with code {res.status_code}")
			self.logger.debug(res.text)
			return []

	'''
	Return np.ndarray for mid-point price candles with open, high, low and close price
	'''
	async def getCandles(self, instrument: str, since: datetime,
	gran: str = 'S5') -> np.ndarray:
		assert gran in ['S5', 'S10', 'S15', 'S30', 'M1', 'M15', 'H1', 'D']

		_ = endpoints.get('candles').format(instrument = instrument)
		url = self.url.format(endpoint = _)
		q = {
			'price': 'M',
			'granularity': gran,
			'from': since.strftime("%s"),
		}

		res = self.session.get(url, params=q)
		if 200 <= res.status_code < 300:
			_ = json.loads(res.text).get('candles', None)

			if not _ or type(_) != list or len(_) == 0:
				self.logger.debug("No candles provide")
				self.logger.debug(res.text)
				raise Exception

			candles = map(
				lambda x:
					[x['mid']['o'], x['mid']['h'], x['mid']['l'], x['mid']['c']],
				_
			)

			return np.array(list(candles)).astype(np.float, copy=False)
		else:
			self.log(f"Get candles with status code {res.status_code}")
			raise Exception
