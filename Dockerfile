FROM localhost/python:latest
WORKDIR /app
COPY access_token /app
COPY app.py /app
COPY trader /app/trader
ENTRYPOINT ["/usr/local/bin/python3"]
CMD ["/app/app.py"]
