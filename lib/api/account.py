import json
import logging

logger = logging.getLogger(__name__)

async def getSummary(wrapper) -> dict:
	_ = "v3/accounts/{accountID}/summary".format(accountID = wrapper.accountID)
	url = wrapper.url.format(endpoint = _)

	res = wrapper.session.get(url)
	if res.status_code == 200:
		_ = json.loads(res.text)
		return _
	else:
		logger.warn('Get account summary fail')
		logger.warn(res.text)
		return {}
