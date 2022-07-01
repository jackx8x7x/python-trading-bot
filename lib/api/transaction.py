import json
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

'''
Get all P/L related transactions since a sinceid, return in list
'''
async def getTransactionsInIdRange(wrapper, sinceID, toID, t) -> list:
	sinceID = str(sinceID)
	toID = str(toID)
	_ = {
		'from': sinceID,
		'to': toID,
		'type':t 
	}
	query = urlencode(_)

	_ = "v3/accounts/{accountID}/transactions/idrange".format(accountID = wrapper.accountID)
	url = wrapper.url.format(endpoint = _) + f'?{query}'

	res = wrapper.session.get(url)
	if res.status_code == 200:
		_ = json.loads(res.text)
		ops = _.get('transactions', [])
		return ops
	else:
		logger.warn(f"getTransactions get response with code {res.status_code}")
		logger.warn(res.text)
		return []
