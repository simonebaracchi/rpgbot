FROM  python:3-alpine

COPY requirements.txt /

RUN pip install -r requirements.txt

RUN mkdir /rpgbot

COPY main.py /rpgbot
COPY db.py /rpgbot
COPY config.py /rpgbot

VOLUME /data

WORKDIR /rpgbot

CMD python /rpgbot/main.py
