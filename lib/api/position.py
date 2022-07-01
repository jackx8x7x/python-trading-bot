import json
import logging

logger = logging.getLogger(__name__)


async def getInstrumentPosition(wrapper, instr: str) -> dict:
	_ = "v3/accounts/{accountID}/positions/{instrument}".format(
			accountID = wrapper.accountID, instrument = instr)
	url = wrapper.url.format(endpoint = _)

	res = wrapper.session.get(url)
	if res.status_code == 200:
		_ = json.loads(res.text)
		position = _.get('position', {})
		return position
	else:
		logger.warn(f"getInstrumentPosition get response with code {res.status_code}")
		logger.warn(res.text)
		return []

'''
Return open positions in list
'''
async def getOpenPositions(wrapper) -> list:
	_ = "v3/accounts/{accountID}/openPositions".format(
		accountID = wrapper.accountID)
	url = wrapper.url.format(endpoint = _)

	res = wrapper.session.get(url)
	if res.status_code == 200:
		_ = json.loads(res.text)
		ops = _.get('positions', [])
		return ops
	else:
		logger.warn(f"getOpenPositions get response with code {res.status_code}")
		logger.warn(res.text)
		return []

'''
Return all history positions in list
'''
async def getAllPositions(wrapper) -> list:
	_ = "v3/accounts/{accountID}/positions".format(
		accountID = wrapper.accountID)
	url = wrapper.url.format(endpoint = _)

	res = wrapper.session.get(url)
	if res.status_code == 200:
		_ = json.loads(res.text)
		positions = _.get('positions', [])
		return positions
	else:
		logger.warn(f"getAllPositions get response with code {res.status_code}")
		logger.warn(res.text)
		return []

async def closePosition(wrapper, instr: str, units) -> dict:
	_ = "v3/accounts/{accountID}/positions/{instrument}/close".format(
			accountID = wrapper.accountID, instrument = instr)
	url = wrapper.url.format(endpoint = _)
	if float(units) < 0:
		data = {"shortUnits": str(-float(units))}
	else:
		data = {"longUnits": units}
	data = json.dumps(data)

	res = wrapper.session.put(url, data=data)
	if res.status_code == 200:
		logger.info(f"Close position {units} {instr}")
		_ = json.loads(res.text)
		return _
	else:
		logger.warn(f"Close position {units} {instr} fail")
		logger.warn(res.text)
		logger.warn(data)
		return None

