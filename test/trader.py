import json
from lib.trader import Trader

config = {}
with open('app.conf', 'r') as f:
	config = json.load(f)

instrConfig = []
with open('instruments.conf', 'r') as f:
	instrConfigs = json.load(f).get('instruments', [])

config['DEMO'] = 1
config['DEBUG'] = 1
trader = Trader(config, instrConfigs)
