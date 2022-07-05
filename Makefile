all:
	python3 app.py -h

.PHONY: demo
demo:
	python3 app.py -D -t

.PHONY: test
test:
	python3 -m unittest -f -b
