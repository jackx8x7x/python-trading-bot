import asyncio
import logging
from datetime import time
from datetime import datetime
from datetime import timezone
from datetime import timedelta
from lib.api import ApiWrapper
from lib.candles import moving_average as ma
from lib.candles import belowCross, aboveCross, upCross, downCross

logger = logging.getLogger(__name__)

'''
instrument config as
{
	'name': "BCO_USD",
	'units': 1,
	'precise', 3
}
'''
class Instrument(ApiWrapper):
	def __init__(self, appConfig, instrumentConfig, trader):
		super().__init__(appConfig)
		self.trader = trader
		self.tradable = 1
		self.state = 0
		self.lastPrice = 0
		self.leverage = appConfig.get('leverage', 20)
		self.maxOpenPositions = appConfig.get('maxOpenPositions', 15)
		self.takeProfit = appConfig.get('takeProfit', 0.002)
		self.stopLoss = appConfig.get('stopLoss', 0.0018)
		self.tradeDelay = appConfig.get('tradeDelay', 10)
		self.tradeInterval = appConfig.get('tradeInterval', 5)
		self.openPositions = {
			'long': {
				'units': '0'
			},
			'short': {
				'units': '0'
			},
		}
		self.__dict__.update(instrumentConfig)

	'''
	units*delta = PL
	units*delta/(last+delta) = PL
	'''
	def getDistance(self, units, pl):
		if not self.lastPrice or units <= 0:
			return 0

		name = self.name
		if name.endswith('_USD'):
			return pl/units
		elif name.startswith('USD_'):
			return pl*self.lastPrice/(units - pl)
		else:
			return 0

	def getUnits(self, amount):
		if not self.lastPrice:
			return 0

		name = self.name

		if name.endswith('_USD'):
			return amount/self.lastPrice
		elif name.startswith('USD_'):
			return amount
		elif name.endswith('_GBP'):
			GBP_USD = self.trader.instruments['GBP_USD'].lastPrice
			if not GBP_USD:
				return 0
			return amount/(GBP_USD*self.lastPrice)
		elif name.startswith('GBP_'):
			GBP_USD = self.trader.instruments['GBP_USD'].lastPrice
			if not GBP_USD:
				return 0
			return amount/GBP_USD
		else:
			return 0

	def now(self):
		now = datetime.now(tz=timezone.utc)
		return now

	'''
	Update instrument state using S5 candles
	M30 > M45 > M60 go long (for at least 3 candle)
	M30 < M45 < M60 go short
	'''
	async def asyncTrade(self):
		while True:
			# Trade between 00:30 UTC to 20:30 UTC
			now = self.now()
			start = time(00, 30, 0)
			end = time(20, 30, 0)
			closeAll = time(20, 35, 0)
			if not (start <= now.time() <= end):
				# Clean open positions
				if now.time() < closeAll:
					await self.closeLong()
					await self.closeShort()
				logger.debug('Not in trade time')
				await asyncio.sleep(15*60)
				continue

			gran = 'M1'
			windows = [5, 15, 45]
			lastCount = 5
			need = max(windows) + lastCount
	
			# Sleep 5 mins if no sufficient candles return
			since = now - timedelta(minutes=need+2)
			try:
				candles = await self.getCandles(self.name, since=since, gran=gran)
			except:
				self.state = 0
				self.lastPrice = 0
				logger.debug('No candles return')
				await asyncio.sleep(60*5)
				continue
			
			candlesCount = candles.shape[0]
			if candlesCount < need:
				logger.debug(
					f"Not sufficient candles {candlesCount} return"
				)
				self.state = 0
				await asyncio.sleep(60*5)
				continue

			trader = self.trader
			marginUsed = trader.accountState.marginUsed
			NAV = trader.accountState.NAV
			if marginUsed/NAV > trader.allowMarginUsed:
				logger.debug("Margin used above")
				await asyncio.sleep(self.tradeDelay)
				continue
	
			self.candles = candles
		
			opens = candles[0:,0]
			highs = candles[0:,1]
			lows = candles[0:,2]
			closes = candles[0:,3]
			self.lastPrice = closes[-1]
			means = (highs + lows)/2

			# calculate the MAs
			x, y, z = windows
			MA1 = ma(means, x)[-lastCount:]
			MA2 = ma(means, y)[-lastCount:]
			MA3 = ma(means, z)[-lastCount:]

			# create order
			amount = (self.leverage * NAV)/self.maxOpenPositions
			units = self.getUnits(amount)
			lastPrice = self.lastPrice
			takeProfit = abs(lastPrice * self.takeProfit)
			stopLoss = abs(lastPrice * self.stopLoss)

			ops = self.openPositions

			# Test if we are in long context
			l = 3
			assert lastCount > l
			d = MA2 - MA3
			op = self.openPositions
			if (MA2 > MA3)[-l:].all():
				if (MA1 < MA3)[-l:].all():
					asyncio.create_task(self.closeLong())
					await asyncio.sleep(self.tradeInterval*60)
					continue
				elif aboveCross(MA1, MA3, 5):
					asyncio.create_task(self.closeLong())
					await asyncio.sleep(self.tradeInterval*60)
					continue

				# First order in long position
				if not op or float(op['long']['units']) == 0:
					if (d[-l:-1] <= d[-l+1:]).all() and (MA1 >= MA2)[-l:].all():
						if (MA1-MA3).max() > takeProfit/2:
							await self.createOrder(units, takeProfit, stopLoss)
							sec = self.tradeInterval*60
							while sec > 0:
								await asyncio.sleep(1)
								sec = sec - 1
								op = self.openPositions
								if not op or float(op['long']['units']) == 0:
									break

				# Add more orders in long position
				else:
					used = float(op.get('marginUsed', 0))
					pl = float(op['unrealizedPL'])
					if used/NAV < 0.1 and (pl > 0.15 or (pl < -0.15 and MA2[-1] >= lastPrice > MA3[-1])):
						await self.createOrder(units, takeProfit, stopLoss)
						await asyncio.sleep(self.tradeInterval*60)

			elif (MA2 < MA3)[-l:].all():
				if (MA1 > MA3)[-l:].all():
					asyncio.create_task(self.closeShort())
					await asyncio.sleep(self.tradeInterval*60)
					continue
				elif belowCross(MA1, MA3, 5):
					asyncio.create_task(self.closeShort())
					await asyncio.sleep(self.tradeInterval*60)
					continue

				if not op or float(op['short']['units']) == 0:
					if (d[-l:-1] >= d[-l+1:]).all() and (MA1 <= MA2)[-l:].all():
						if -(MA1-MA3).min() > takeProfit/2:
							await self.createOrder(-units, takeProfit, stopLoss)
							sec = self.tradeInterval*60
							while sec > 0:
								await asyncio.sleep(1)
								sec = sec - 1
								op = self.openPositions
								if not op or float(op['short']['units']) == 0:
									break

				else:
					used = float(op.get('marginUsed', 0))
					pl = float(op['unrealizedPL'])
					if used/NAV < 0.1 and (pl > 0.15 or (pl < -0.15 and MA2[-1] <= lastPrice < MA3[-1])):
						await self.createOrder(-units, takeProfit, stopLoss)
						await asyncio.sleep(self.tradeInterval*60)

			await asyncio.sleep(self.tradeDelay)

	async def createOrder(self, units=0, takeProfit=0, stopLoss=0):
		if not self.tradable:
			logger.info(f"{self.name} not tradable")
			return

		name = self.name

		_ = self.unit
		if _ == 1:
			units = "%.0f" % units
		elif _ == 0.1:
			units = "%.1f" % units
		else:
			logger.info(f"Wrong unit config for {name}")
			return

		_ = self.precise
		take = "%.*f" % (_, takeProfit)
		stoploss = "%.*f" % (_, stopLoss)

		if float(units) == 0 or float(take) == 0 or float(stoploss) == 0:
			return

		self.log(f"create order {units} {self.name}@{self.lastPrice} P/L {take}/{stoploss}")
		await self.createMarketOrder(name, units=units, take=take, stoploss=stoploss)

	async def closePosition(self, units):
		return await super().closePosition(self.name, units)
	
	async def closeLong(self):
		if ('long' in self.openPositions
		and float(self.openPositions['long']['units']) != 0):
			units = self.openPositions['long']['units']
			await self.closePosition(units)

	async def closeShort(self):
		if ('short' in self.openPositions
		and float(self.openPositions['short']['units']) != 0):
			units = self.openPositions['short']['units']
			await self.closePosition(units)
