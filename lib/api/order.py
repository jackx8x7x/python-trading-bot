import json
import logging

logger = logging.getLogger(__name__)

'''
Create a market order for specified instrument, units, takeprofit and
stoploss in distance
'''
async def createMarketOrder(wrapper, instr: str, units: str, take: str,
stoploss: str):
	_ = "v3/accounts/{accountID}/orders".format(accountID = wrapper.accountID)
	url = wrapper.url.format(endpoint = _)

	if float(units) == 0 or float(take) == 0 or float(stoploss) == 0:
		logger.debug("Create order with 0 units, takeprofit or stoploss")
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
	res = wrapper.session.post(url, data=data)
	if res.status_code == 201:
		_ = json.loads(res.text)
		return _
	else:
		logger.warn(f"Create order fail {res.text}")
		return {}
