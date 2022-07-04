import json
import logging

logger = logging.getLogger(__name__)

'''
Return a list of open trades
'''
async def getOpenTrades(wrapper) -> list:
	_ = "v3/accounts/{accountID}/openTrades".format(
			accountID = wrapper.accountID)
	url = wrapper.url.format(endpoint = _)

	res = wrapper.session.get(url)
	if res.status_code == 200:
		_ = json.loads(res.text)
		trades = _.get('trades', {})
		return trades
	else:
		logger.warn(f"getOpenTrades get response with code {res.status_code}")
		logger.warn(res.text)
		return []

'''
Close a open trade with ID
'''
async def closeOpenTrade(wrapper, tradeID):
	assert type(int(tradeID)) == int
	_ = "v3/accounts/{accountID}/trades/{tradeID}/close".format(
		accountID = wrapper.accountID, tradeID = tradeID)
	url = wrapper.url.format(endpoint = _)

	res = wrapper.session.put(url)
	status = res.status_code
	if status == 200:
		_ = json.loads(res.text)
		ops = _.get('positions', [])
	elif status == 404:
		logger.info(f"Trade {tradeID} not exists")
	else:
		logger.warn(f"getOpenPositions get response with code {status}")
		logger.warn(res.text)
