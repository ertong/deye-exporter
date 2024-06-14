FROM python:3.12

USER root
WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

ENV TZ=Europe/Kiev

COPY . /app

WORKDIR /app

CMD [ "python3", "./main.py" ]
