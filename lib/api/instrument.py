import json
import logging
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

'''
Return mid-point price candles with open, high, low and close price in np.ndarray
'''
async def getCandles(wrapper, instrument: str, since: datetime, gran: str = 'S5') -> np.ndarray:
	assert gran in ['S5', 'S10', 'S15', 'S30', 'M1', 'M15', 'H1', 'D']

	_ = "v3/instruments/{instrument}/candles".format(instrument = instrument)
	url = wrapper.url.format(endpoint = _)
	q = {
		'price': 'M',
		'granularity': gran,
		'from': since.strftime("%s"),
	}

	res = wrapper.session.get(url, params=q)
	if 200 <= res.status_code < 300:
		_ = json.loads(res.text).get('candles', None)

		if not _ or type(_) != list or len(_) == 0:
			logger.debug("No candles provide")
			logger.debug(res.text)
			raise Exception

		candles = map(
			lambda x:
				[x['mid']['o'], x['mid']['h'], x['mid']['l'], x['mid']['c']],
			_
		)

		return np.array(list(candles)).astype(np.float, copy=False)
	else:
		logger.warn(f"Get candles with status code {res.status_code}")
		raise Exception
