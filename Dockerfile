FROM python:3.7-slim

MAINTAINER James Boyce <mail@its-jam.es> 

COPY resources/population.json resources/population.json
COPY *.py .
COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "post_covid_stats.py"]