import json
import requests
import os
from typing import Dict, List
from slack_sdk.web import SlackResponse
from slack_bot import CovidSlackBot

SELECTED_CODES = os.environ.get("SELECTED_CODES", 'AUS,VIC,NSW')
POPULATION_BRACKET = os.environ.get("POPULATION_BRACKET", "16+")
SLACK_CHANNEL_NAME = os.environ.get("SLACK_CHANNEL_NAME", "#testcovidbot")
SLACK_BOT_DISPLAY = os.environ.get("SLACK_BOT_DISPLAY", 'CODE_DATA,VAX_DATA')
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", '')
SLACK_BOT_EMOJI = os.environ.get("SLACK_BOT_EMOJI", ":robot_face:")
SLACK_BOT_NAME = os.environ.get("SLACK_BOT_NAME", "CovidLiveSummary")


def post_covid_stats() -> SlackResponse:
    state_data_file: str = "resources/state-data.json"
    source_url: str = "https://covidlive.com.au/covid-live.json"
    covid_data: Dict = fetch_and_parse_data(source_url)
    
    with open(state_data_file) as stateDataFile:
        state_data: Dict = json.load(stateDataFile)
    
    slack_bot: CovidSlackBot = CovidSlackBot(
        SLACK_BOT_TOKEN,
        SLACK_CHANNEL_NAME,
        SLACK_BOT_NAME,
        SLACK_BOT_EMOJI
    )

    response: SlackResponse
    codes = SELECTED_CODES.split(",")
    display = SLACK_BOT_DISPLAY.split(",")

    if "CODE_DATA" in display:
        code_data: Dict = get_most_recent_data_for_codes(covid_data, state_data, codes, POPULATION_BRACKET)
        response = slack_bot.execute_for_covid_data(code_data)
    if "VAX_DATA" in display:
        vax_data: Dict = get_vax_data_for_codes(covid_data, state_data, codes, POPULATION_BRACKET)
        response = slack_bot.execute_for_vax_stats(vax_data)

    if response.status_code != 200:
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


def get_vax_data_for_codes(data: Dict, state_data: Dict, codes: List[str], population_bracket: str) -> Dict:
    vax_data: Dict[str] = {}

    for row in data:
        if(row['CODE'] in codes):
            code: str = row['CODE']
            # If we dont have this state in the most recent data add it
            if code not in vax_data:
                if row["LAST_UPDATED_DATE"] != None and row['VACC_DOSE_CNT'] != None:
                    vax_data[code] = row
                    
                    vax_data[code]["RECORD_COUNT"] = 0
                    vax_data[code]["POPULATION_BRACKET"] = population_bracket
                    vax_data[code]["CODE_EMOJI"] = state_data[code]["EMOJI"]
                    vax_data[code]["POPULATION"] = state_data[code]["POPULATION"][population_bracket]

                    normalise_vax_data_for_population(vax_data[code], population_bracket)
                    print(f'Code: {code} latest vax data selected for updated date: {row["LAST_UPDATED_DATE"]}')
                continue

            current = vax_data[code]
            if current["RECORD_COUNT"] < 7: #weekly average
                current["RECORD_COUNT"] += 1
                normalise_vax_data_for_population(row, population_bracket);
                current["PREV_VACC_FIRST_DOSE_CNT"] = row["VACC_FIRST_DOSE_CNT"]
                current["PREV_VACC_PEOPLE_CNT"] = row["VACC_PEOPLE_CNT"]

    return vax_data

def normalise_vax_data_for_population(data: Dict, population_bracket: str):
    if population_bracket == "16+": # subtract the 12 - 15 jabs
        youthFirstVax: int = int(data["VACC_FIRST_DOSE_CNT_12_15"])
        youthFullVax: int = int(data["VACC_PEOPLE_CNT_12_15"])

        # fallback on previous vax if 0. Datafeed seems to update current vax with 
        # yesterdays data but not 12-15, so this should be accurate (enough)
        if youthFirstVax == 0:
            youthFirstVax = int(data["PREV_VACC_FIRST_DOSE_CNT_12_15"])

        if youthFullVax == 0:
            youthFullVax = int(data["PREV_VACC_PEOPLE_CNT_12_15"])

        data["VACC_FIRST_DOSE_CNT"] = int(data["VACC_FIRST_DOSE_CNT"]) - youthFirstVax
        data["VACC_PEOPLE_CNT"] = int(data["VACC_PEOPLE_CNT"]) - youthFullVax

def get_most_recent_data_for_codes(data: Dict, state_data: Dict, codes: List[str], population_bracket: str) -> Dict:
    most_recent_data: Dict[str] = {}

    for row in data:
        if(row['CODE'] in codes):
            # If we dont have this state in the most recent data add it
            if row['CODE'] not in most_recent_data:
                if row["LAST_UPDATED_DATE"] != None:
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
            
            if current['VACC_DOSE_CNT'] == None and row['VACC_DOSE_CNT'] != None:
                #vaccination data hasn't updated - just use previous
                current['PREV_VACC_DOSE_CNT'] = row['PREV_VACC_DOSE_CNT']
                current['VACC_DOSE_CNT'] = row['VACC_DOSE_CNT']
                current['PREV_VACC_FIRST_DOSE_CNT'] = row['PREV_VACC_FIRST_DOSE_CNT']
                current['VACC_FIRST_DOSE_CNT'] = row['VACC_FIRST_DOSE_CNT']
                current['PREV_VACC_PEOPLE_CNT'] = row['PREV_VACC_PEOPLE_CNT']
                current['VACC_PEOPLE_CNT'] = row['VACC_PEOPLE_CNT']
                
    for code in codes:
        most_recent_data[code]["POPULATION_BRACKET"] = population_bracket
        if code not in state_data:
            most_recent_data[code]["POPULATION"] = None
            continue

        most_recent_data[code]["POPULATION"] = state_data[code]["POPULATION"][population_bracket]

    return most_recent_data

if __name__ == "__main__":
    post_covid_stats()
