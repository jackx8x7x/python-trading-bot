import unittest
import json
from .trader import trader

def dump(o):
	return json.dumps(o, indent=2)

class TestCloseAllTrade(unittest.IsolatedAsyncioTestCase):
	async def test_getOpenTrades(self):
		openTrades = await trader.getOpenTrades()

		for o in openTrades:
			print(f"Close order {o.get('id')}")
			await trader.closeOpenTrade(o.get('id'))

		openTrades = await trader.getOpenTrades()
		self.assertEqual(openTrades, [])

if __name__ == '__main__':
	unittest.main()
