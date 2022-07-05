# Python-Trading-Bot
An [Oanda v20 API](https://developer.oanda.com/rest-live-v20/introduction/) trading-bot which may lose your money

An hobby project using Python asyncio and requests modules to trade with Oanda v20 API

***Warning! Don't use this project to trade***
## Configuration
---
Fill the token and account ID values in file app.conf

```bash
$ mv conf/sample-app.conf conf/app.conf
$ vi conf/app.conf
```

## Run
---
### Python
```bash
usage: app.py [-h] [-d] [-D] [-t] [-l LOGFILE] [-r]

A trading-bot using OANDA v20 API

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Run in the debug mode
  -D, --demo            Run in the demo mode
  -t, --textui          Run in the text-ui mode
  -l LOGFILE, --log LOGFILE
                        Log into file LOGFILE
  -r, --report          Run in the report only mode and not to trade
```
### Docker
Not test yet...

## Components
---
### API wrapper
- Using Python `requests` module
### Class Trader
- Updates and monitoring account state
### Class Instrument
- Retrieve instrument's price information
- Creates market order on some strategy
- Provides method to load custom strategies ***(under development)***
### UI
Using `curses`
## Todo
---
- Rule based decision and trading system
  - Use a set of custom user-defined rules and current trading state to make decision and trade
- Custom strategy loading support
- Define a language to describe a loadable module
## Theory
---
### Probability
- Say we have trade $N$ instruments $M_i$, $i$ in $1,...,N$ with amount $f_i$, and probabilities $P(Profit|t_i, s_i)$ as $P_i$, $P(Loss|t_i, s_i)$ as $Q_i$ to gain a given takeprofit $t_i/unit$ and loss stoploss $s_i/unit$ in a given time interval
> Note that $Q_i$ may not equal to $1 - P_i$, i.e, the takeprofit/stoploss order may not be filled in the given time
- Then the expections of our gain in the given time interval is

$$
E=\sum_{i=1}^N f_i(P_k t_k - Q_k s_k)
$$

and our goal is to maxisum this expection with strategy to determine units $f_i$, takeprofit $t_i$ and stoploss $s_i$ to trade
### Kelly criterion
## Demo
---
<img width="1726" alt="demo" src="https://user-images.githubusercontent.com/43628402/176477007-6639ed03-e12f-49eb-bf2a-86582b768d61.png">

## Tags
---
#Oanda, #trading-bot, #bot, #forex, #CFD, #trading, #robot
