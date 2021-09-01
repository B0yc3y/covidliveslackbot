import json
import requests
from typing import Dict, List
import os
from slack_sdk import WebClient
from ssl import SSLContext

SELECTED_CODES = os.environ.get("SELECTED_CODES", 'VIC,NSW')
SLACK_CHANNEL_NAME = os.environ.get("SLACK_CHANNEL_NAME", "#testcovidbot")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", '')
SLACK_BOT_EMOJI = os.environ.get("SLACK_BOT_EMOJI", ":robot_face:")
SLACK_BOT_NAME = os.environ.get("SLACK_BOT_NAME", "CovidLiveSummary")

SLACK_CLIENT = WebClient(
    token=SLACK_BOT_TOKEN,
    ssl=SSLContext(),
)

def main():
    local_file = "covid-live.json"
    url = "https://covidlive.com.au/covid-live.json"
    fetch_data(url, local_file)

    # read file
    with open(local_file, 'r') as myfile:
        # parse file
        covid_data: Dict = json.load(myfile)

    most_recent_data: Dict[str] = get_most_recent_data_for_codes(covid_data, SELECTED_CODES.split(","))
    generated_message_text: List[str] = [ generate_group_message(most_recent_data[group]) for _, group in enumerate(most_recent_data) ]
    
    print("Posting stats to slack")

    response = SLACK_CLIENT.chat_postMessage(
        channel = SLACK_CHANNEL_NAME,
        text = "COVID stats updated",
        blocks = generate_slack_message_blocks(generated_message_text),
        username = SLACK_BOT_NAME,
        icon_emoji = SLACK_BOT_EMOJI,
    )
        
    if response.status_code is not 200:
        print(f"something went wrong: {response.data}")
        exit(1)

    print(response.data)
    print(f"Successfully posted update to slack")
    exit(0)

def fetch_data(url: str, outfile: str):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Unable to fetch data: {response.text}")
        exit(1)

    print(f"Writing data to file: {url}")
    with open(outfile, "w") as file1:
        # Writing data to a file
        file1.write(response.text)

def generate_slack_message_blocks(messages: List[str]) -> List[Dict]:
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        } for message in messages
    ]
    
def generate_group_message(group: Dict) -> str:
    # prepare the variables
    new_cases: str = None
    if group['CASE_CNT'] is not None:
        new_cases = int(group['CASE_CNT']) - int(group['PREV_CASE_CNT'])

    new_oseas_cases: str = None
    if group['SRC_OVERSEAS_CNT'] is not None:
        new_oseas_cases = int(group['SRC_OVERSEAS_CNT']) - int(group['PREV_SRC_OVERSEAS_CNT'])

    new_tests: str = None
    if group['TEST_CNT'] is not None:
        new_tests = int(group['TEST_CNT']) - int(group['PREV_TEST_CNT'])

    new_deaths: str = None
    if group['DEATH_CNT'] is not None:
        new_deaths = int(group['DEATH_CNT']) - int(group['PREV_DEATH_CNT'])

    new_vax: str = None
    if group['VACC_DOSE_CNT'] is not None:
        new_vax  = int(group['VACC_DOSE_CNT']) - int(group['PREV_VACC_DOSE_CNT'])
    
    active_case_change: str = None
    if group['ACTIVE_CNT'] is not None:
        active_case_change  = int(group['ACTIVE_CNT']) - int(group['PREV_ACTIVE_CNT'])
    
    hosp_change: str = None
    if group['MED_HOSP_CNT'] is not None:
        hosp_change  = int(group['MED_HOSP_CNT']) - int(group['PREV_MED_HOSP_CNT'])
    
    vent_change: str = None
    if group['MED_VENT_CNT'] is not None:
        vent_change  = int(group['MED_VENT_CNT']) - int(group['PREV_MED_VENT_CNT'])
    
    icu_change: str = None
    if group['MED_ICU_CNT'] is not None:
        icu_change = int(group['MED_ICU_CNT']) - int(group['PREV_MED_ICU_CNT'])

    # Generate the message
    message = f"--- *Latest COVID figures for {group['CODE']}* ---\n"

    if new_cases is not None: 
        message += f":helmet_with_white_cross: {format(new_cases, ',d')} New total cases"

        if active_case_change is not None and active_case_change != 0: 
            message += f" | {format(int(group['ACTIVE_CNT']), ',d')} active cases ({'+' if int(active_case_change) >= 0 else '-'}{format(active_case_change, ',d')})"

        message += "\n"
    

    if new_oseas_cases is not None: 
        message += f":earth_asia: {format(new_oseas_cases, ',d')} New overseas cases\n"
    


    if group['MED_HOSP_CNT'] is not None: 
        message += f":hospital: {format(int(group['MED_HOSP_CNT']), ',d')}"

        if hosp_change is not None:
            message += f" ({'+' if int(hosp_change) >= 0 else '-'}{format(hosp_change, ',d')})"

        message += " Hospitalised"
        
        if group['MED_ICU_CNT'] is not None: 
            message += f" | {format(int(group['MED_ICU_CNT']), ',d')}"

            if icu_change is not None:
                message += f" ({'+' if int(icu_change) >= 0 else '-'}{format(icu_change, ',d')})"

            message += " in ICU"
        
        if group['MED_VENT_CNT'] is not None: 
            message += f" | {format(int(group['MED_VENT_CNT']), ',d')}"

            if vent_change is not None:
                message += f" ({'+' if int(vent_change) >= 0 else '-'}{format(vent_change, ',d')})"

            message += " ventilated"
            
        message += "\n"

    
    if new_deaths is not None: 
        message += f":skull: +{format(new_deaths, ',d')} Deaths"

        if group['DEATH_CNT'] is not None and group['DEATH_CNT'] != 0: 
            message += f" | {format(int(group['DEATH_CNT']), ',d')} Total COVID Deaths"

        message += "\n"
    

    if new_tests is not None: 
        message += f":test_tube: +{format(new_tests, ',d')} Tests in the last reporting period"

        if group['TEST_CNT'] is not None and group['TEST_CNT'] != 0: 
            message += f" | {format(int(group['TEST_CNT']), ',d')} total tests"

        message += "\n"

    
    if new_vax is not None: 
        message += f":syringe: {format(new_vax, ',d')} New Doses"

        if group["VACC_DOSE_CNT"] is not None and group["VACC_DOSE_CNT"] != 0: 
            message += f" | {format(int(group['VACC_DOSE_CNT']), ',d')} in total"
        
        if group["VACC_FIRST_DOSE_CNT"] is not None and group["VACC_FIRST_DOSE_CNT"] != 0: 
            message += f" | {format(int(group['VACC_FIRST_DOSE_CNT']), ',d')} 1st dose"

        if group["VACC_PEOPLE_CNT"] is not None and group["VACC_PEOPLE_CNT"] != 0: 
            message += f" | {format(int(group['VACC_PEOPLE_CNT']), ',d')} Fully Vaxed"

        message += " (This will often be incorrect as GP numbers come in at odd times)\n"


    if group["REPORT_DATE"] is not None and group["LAST_UPDATED_DATE"]: 
        message += f":robot_face: {group['REPORT_DATE']} Report date, using covidlive.com.au data published at: {group['LAST_UPDATED_DATE']} AEST"
    
    return message

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
    main()
