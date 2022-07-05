import json
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

'''
Get instruments' prices
'''
async def getInstrumentPrices(wrapper, instruments: list) -> list:
	_ = {
		'instruments': ','.join(instruments),
	}
	query = urlencode(_)

	_ = "v3/accounts/{accountID}/pricing".format(accountID = wrapper.accountID)
	url = wrapper.url.format(endpoint = _) + f'?{query}'

	res = wrapper.session.get(url)
	if res.status_code == 200:
		_ = json.loads(res.text)
		ops = _.get('prices', [])
		return ops
	else:
		logger.warn(f"getInstrumentPrices get response with code {res.status_code}")
		logger.warn(res.text)
		return []
