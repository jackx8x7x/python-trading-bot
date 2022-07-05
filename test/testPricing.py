import unittest
import json
from .trader import trader

def dump(o):
	return json.dumps(o, indent=2)

class TestCloseAllTrade(unittest.IsolatedAsyncioTestCase):
	async def test_getInstrumentPrices(self):
		instruments = ['BCO_USD', 'UK100_GBP', 'NAS100_USD']
		prices = await trader.getInstrumentPrices(instruments)

		print(dump(prices))
		self.assertTrue(isinstance(prices, list))
		self.assertEqual(len(prices), len(instruments))

if __name__ == '__main__':
	unittest.main()
