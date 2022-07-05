import json
from lib.trader import Trader

config = {}
with open('app.conf', 'r') as f:
	config = json.load(f)

config['DEMO'] = 1
config['DEBUG'] = 1
trader = Trader(config)
