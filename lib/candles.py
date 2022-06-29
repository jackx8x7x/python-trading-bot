import numpy as np

class Candles:
	def __init__(self, ar):
		self.open = ar[0:,0]
		self.high = ar[0:,1]
		self.low = ar[0:,2]
		self.close = ar[0:,3]

'''
Return array of len(candles) - window + 1
'''
def moving_average(c, window: int=15):
	assert len(c) >= window
	assert 0 < window < 100

	l = len(c)
	resLen = l - window + 1
	res = np.zeros(resLen)

	for i in range(window):
		res = res + c[window-1-i:l-i]

	return res/window

'''
Return true if candles x cross above y from below
i) x go ascend
ii) x cross y from below
'''
def belowCross(x, y, l=3):
	assert l % 2 == 1
	tail = int(l/2)
	if (x[-l:-1] <= x[-l+1:]).all():
		d = x[-l:]-y[-l:]
		if (d[:tail] < 0).all() and (d[-tail:] > 0).all():
			return True
	return False

'''
Return true if candles x cross above y from above
i) x go descend
ii) x cross y from above
'''
def aboveCross(x, y, l=3):
	assert l % 2 == 1
	tail = int(l/2)
	if (x[-l:-1] >= x[-l+1:]).all():
		d = x[-l:]-y[-l:]
		if (d[:tail] > 0).all() and (d[-tail:] < 0).all():
			return True

'''
Return true if candles x cross y below and both x and y ascend
i) Both x and y go ascend
ii) x cross y from below
'''
def upCross(x, y, l=5):
	if ((x[-l:-1] <= x[-l+1:]).all()
	and (y[-l:-1] <= y[-l+1:]).all()):
		d = x[-l:]-y[-l:]
		if (d[:2] < 0).all() and (d[-2:] > 0).all():
			return True
	return False

'''
Return true if candles x cross y below and both x and y ascend
i) Both x and y go ascend
ii) x cross y from below
'''
def downCross(x, y, l=5):
	if ((x[-l:-1] >= x[-l+1:]).all()
	and (y[-l:-1] >= y[-l+1:]).all()):
		d = x[-l:]-y[-l:]
		if (d[:2] < 0).all() and (d[-2:] > 0).all():
			return True
	return False
