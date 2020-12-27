FROM python:3.7-alpine
RUN apk add --no-cache --update gcc g++ make libffi-dev openssl-dev
WORKDIR /usr/src/app
EXPOSE 888
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY config.json server.py utils.py mqtt.py ./
ENV LOGLEVEL=INFO
ENTRYPOINT ["python3"]
CMD ["server.py"]

