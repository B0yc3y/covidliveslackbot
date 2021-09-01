FROM python:3.7-slim

MAINTAINER James Boyce <mail@its-jam.es> 

COPY covid_slack_bot.py covid_slack_bot.py
COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "covid_slack_bot.py"]