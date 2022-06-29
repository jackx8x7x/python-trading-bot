# MoneyLoser
An Oanda v20 API trading robot which may lose your money

An simple project using Python asyncio and requests modules to trade with Oanda v20 API

***Warning! Don't use this project to trade***
## Configuration
---
Fill the token and account ID values in file app.conf

```bash
$ mv sample-app.conf app.conf
$ vi app.conf
```

## Run
---
### Python
```bash
$ python3 app.py -h
python3 app.py -h
usage: app.py [-h] [-d] [-D] [-t] [-l LOGFILE]

Oanda v20 API trader

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Run in the debug mode
  -D, --demo            Run in the demo mode
  -t, --textui          Run in the text-ui mode
  -l LOGFILE, --log LOGFILE
                        Log into file LOGFILE
```
### Docker
Not test yet...

## Components
---
### API wrapper
Using Python `requests` module
### UI
Using `curses`

## Demo
---
<img width="1726" alt="demo" src="https://user-images.githubusercontent.com/43628402/176477007-6639ed03-e12f-49eb-bf2a-86582b768d61.png">