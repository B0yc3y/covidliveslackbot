import json
import requests
import os
from typing import Dict, List
from slack_sdk.web import SlackResponse
from slack_bot import CovidSlackBot

SELECTED_CODES = os.environ.get("SELECTED_CODES", 'VIC,NSW')
SLACK_CHANNEL_NAME = os.environ.get("SLACK_CHANNEL_NAME", "#testcovidbot")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", '')
SLACK_BOT_EMOJI = os.environ.get("SLACK_BOT_EMOJI", ":robot_face:")
SLACK_BOT_NAME = os.environ.get("SLACK_BOT_NAME", "CovidLiveSummary")


def post_covid_stats() -> SlackResponse:
    source_url: str = "https://covidlive.com.au/covid-live.json"
    covid_data: Dict = fetch_and_parse_data(source_url)

    slack_bot: CovidSlackBot = CovidSlackBot(
        SLACK_BOT_TOKEN,
        SLACK_CHANNEL_NAME,
        SLACK_BOT_NAME,
        SLACK_BOT_EMOJI
    )
    code_data: Dict = get_most_recent_data_for_codes(covid_data, SELECTED_CODES.split(","))
    response: SlackResponse = slack_bot.execute_for_codes(code_data)

    if response.status_code is not 200:
        print(f"something went wrong: {response.data}")
        exit(1)

    print(response.data)
    print(f"Successfully posted update to slack")
    return response


def fetch_and_parse_data(source_url: str):
    # fetch json content
    response_body: str = fetch_data(source_url)
    # return parsed content
    return json.loads(response_body)


def fetch_data(url: str):
    print(f"Fetching data from: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Unable to fetch data: {response.text}")
        exit(1)

    print(f"Successfully fetched")
    return response.text


def get_most_recent_data_for_codes(data: Dict, codes: List[str]) -> Dict:
    most_recent_data: Dict[str] = {}

    for row in data:
        if(row['CODE'] in codes):
            # If we dont have this state in the most recent data add it
            if row['CODE'] not in most_recent_data:
                most_recent_data[row['CODE']] = row
                print(f'Code: {row["CODE"]} data selected for updated date: {row["LAST_UPDATED_DATE"]}')
                continue

            current = most_recent_data[row['CODE']]
            
            if row['REPORT_DATE'] > current['REPORT_DATE']:
                print(f'Code: {row["CODE"]} data selected for updated date: {row["LAST_UPDATED_DATE"]}')
                most_recent_data[row['CODE']] = row
                continue

            if row['REPORT_DATE'] == current['REPORT_DATE'] and row['LAST_UPDATED_DATE'] >= current['LAST_UPDATED_DATE']:
                most_recent_data[row['CODE']] = row
                print(f'Code: {row["CODE"]} data selected for updated date: {row["LAST_UPDATED_DATE"]}')
                continue

    return most_recent_data


if __name__ == "__main__":
    post_covid_stats()