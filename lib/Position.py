class Position:
	def __init__(self, name):
		self.instrument = name
		self.update(
			{'instrument': name}
		)

	def update(self, data):
		assert self.instrument == data.get('instrument', '')

		self.pl = float(data.get('pl', 0))
		self.unrealizedPL = float(data.get('unrealizedPL', 0))
		self.marginUsed = float(data.get('marginUsed', 0))

		longData = data.get('long', {})
		shortData = data.get('short', {})
		self.long = PositionSide(longData)
		self.short = PositionSide(shortData)

class PositionSide():
	def __init__(self, data):
		self.units = float(data.get('units', 0))
		self.averagePrice = float(data.get('averagePrice', 0))
		self.tradeIDs = data.get('tradeIDs', [])
		self.pl = float(data.get('pl', 0))
		self.unrealizedPL = float(data.get('unrealizedPL', 0))
