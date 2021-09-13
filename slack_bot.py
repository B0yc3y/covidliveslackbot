from ssl import SSLContext
from typing import List, Dict
from slack_sdk import WebClient
from slack_sdk.web import SlackResponse


class CovidSlackBot:

    def __init__(self, slack_token: str, channel_name: str, bot_name: str, emoji: str) -> None:
        self.channel_name: str = channel_name
        self.bot_name: str = bot_name
        self.emoji: str = emoji
        self.client: WebClient = WebClient(
            token=slack_token,
            ssl=SSLContext()
        )

    def post_messages_to_slack(self, messages: List[str]) -> SlackResponse:
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            } for message in messages
        ]

        print("Posting stats to slack")

        return self.client.chat_postMessage(
            channel=self.channel_name,
            text="COVID stats updated",
            username=self.bot_name,
            icon_emoji=self.emoji,
            blocks=blocks
        )

    # For the filtered data, generate messages and send them to slack
    def execute_for_codes(self, covid_data: Dict) -> SlackResponse:
        # Generate the messages for each state/country code
        messages: List[str] = []
        for code_data in covid_data:
            messages.append(self.generate_message_for_code(covid_data[code_data]))

        # Post these messages to slack
        return self.post_messages_to_slack(messages)

    def generate_message_for_code(self, code_data: Dict) -> str:
        # prepare the new data from the previous and current values provided in the payload

        # Total new cases
        new_cases: int = None
        if code_data['CASE_CNT'] is not None:
            new_cases = int(code_data['CASE_CNT']) - int(code_data['PREV_CASE_CNT'])

        # New cases sourced overseas 
        new_oseas_cases: int = None
        if code_data['SRC_OVERSEAS_CNT'] is not None:
            new_oseas_cases = int(code_data['SRC_OVERSEAS_CNT']) - int(code_data['PREV_SRC_OVERSEAS_CNT'])

        # New tests in reporting period
        new_tests: int = None
        if code_data['TEST_CNT'] is not None:
            new_tests = int(code_data['TEST_CNT']) - int(code_data['PREV_TEST_CNT'])

        # New tests in reporting period
        new_deaths: int = None
        if code_data['DEATH_CNT'] is not None:
            new_deaths = int(code_data['DEATH_CNT']) - int(code_data['PREV_DEATH_CNT'])

        # New vaccinations in reporting period
        new_vax: int = None
        if code_data['VACC_DOSE_CNT'] is not None:
            new_vax = int(code_data['VACC_DOSE_CNT']) - int(code_data['PREV_VACC_DOSE_CNT'])

        # Change in the number of active cases
        active_case_change: int = None
        if code_data['ACTIVE_CNT'] is not None:
            active_case_change = int(code_data['ACTIVE_CNT']) - int(code_data['PREV_ACTIVE_CNT'])

        # Change in the number of people in hospital
        hosp_change: int = None
        if code_data['MED_HOSP_CNT'] is not None:
            hosp_change = int(code_data['MED_HOSP_CNT']) - int(code_data['PREV_MED_HOSP_CNT'])

        # Change in the number of people on ventilators
        vent_change: int = None
        if code_data['MED_VENT_CNT'] is not None:
            vent_change = int(code_data['MED_VENT_CNT']) - int(code_data['PREV_MED_VENT_CNT'])

        # Change in the number of people in the ICU
        icu_change: int = None
        if code_data['MED_ICU_CNT'] is not None:
            icu_change = int(code_data['MED_ICU_CNT']) - int(code_data['PREV_MED_ICU_CNT'])

        # Generate a string message in slack markdown, hiding sections depending on available data
        message = f"--- *Latest COVID figures for {code_data['CODE']}* ---\n"

        # Depending on available data attempt to generate cases string in the format below 
        # 1,279 New total cases | 20,148 active cases (+1,108)
        if new_cases is not None:
            message += f":helmet_with_white_cross: {format(new_cases, ',d')} New total cases"

            if active_case_change is not None and active_case_change != 0:
                message += f" | {format(int(code_data['ACTIVE_CNT']), ',d')} active cases ({'+' if int(active_case_change) >= 0 else ''}{format(active_case_change, ',d')})"

            message += "\n"

        # Depending on available data attempt to generate oversaes cases string in the format below 
        # 0 New overseas cases
        if new_oseas_cases is not None:
            message += f":earth_asia: {format(new_oseas_cases, ',d')} New overseas cases\n"

        # Depending on available data attempt to generate oversaes cases string in the format below 
        # 957 (+49) Hospitalised | 160 (+10) in ICU | 64 (-2) ventilated
        if code_data['MED_HOSP_CNT'] is not None:
            message += f":hospital: {format(int(code_data['MED_HOSP_CNT']), ',d')}"

            if hosp_change is not None:
                message += f" ({'+' if int(hosp_change) >= 0 else ''}{format(hosp_change, ',d')})"

            message += " Hospitalised"

            if code_data['MED_ICU_CNT'] is not None:
                message += f" | {format(int(code_data['MED_ICU_CNT']), ',d')}"

                if icu_change is not None:
                    message += f" ({'+' if int(icu_change) >= 0 else ''}{format(icu_change, ',d')})"

                message += " in ICU"

            if code_data['MED_VENT_CNT'] is not None:
                message += f" | {format(int(code_data['MED_VENT_CNT']), ',d')}"

                if vent_change is not None:
                    message += f" ({'+' if int(vent_change) >= 0 else ''}{format(vent_change, ',d')})"

                message += " ventilated"

            message += "\n"

        # Depending on available data attempt to generate deaths string in the format below 
        # +0 Deaths | 822 Total COVID Deaths
        if new_deaths is not None:
            message += f":skull: +{format(new_deaths, ',d')} Deaths"

            if code_data['DEATH_CNT'] is not None and code_data['DEATH_CNT'] != 0:
                message += f" | {format(int(code_data['DEATH_CNT']), ',d')} Total COVID Deaths"

            message += "\n"

        # Depending on available data attempt to generate tests string in the format below 
        # +48,372 Tests in the last reporting period | 9,647,579 total tests
        if new_tests is not None:
            message += f":test_tube: +{format(new_tests, ',d')} Tests in the last reporting period"

            if code_data['TEST_CNT'] is not None and code_data['TEST_CNT'] != 0:
                message += f" | {format(int(code_data['TEST_CNT']), ',d')} total tests"

            message += "\n"

        # Depending on available data attempt to generate vaccinations string in the format: 
        # 12,046 New doses | 466,621 total | 78.2% 1st dose | 42.2% 2nd dose
        # (This will often be incorrect as GP numbers come in at odd times)
        if new_vax is not None:
            message += f":syringe: {format(new_vax, ',d')} New doses"

            if code_data["VACC_DOSE_CNT"] is not None and code_data["VACC_DOSE_CNT"] != 0:
                message += f" | {format(int(code_data['VACC_DOSE_CNT']), ',d')} total"

            if code_data["VACC_FIRST_DOSE_CNT"] is not None and code_data["VACC_FIRST_DOSE_CNT"] != 0:
                message += f" | {format(int(code_data['VACC_FIRST_DOSE_CNT'])/int(code_data['POPULATION']), ',.1%')} {code_data['POPULATION_BRACKET']} 1st dose"

            if code_data["VACC_PEOPLE_CNT"] is not None and code_data["VACC_PEOPLE_CNT"] != 0:
                message += f" | {format(int(code_data['VACC_PEOPLE_CNT'])/int(code_data['POPULATION']), ',.1%')} {code_data['POPULATION_BRACKET']} 2nd dose"

            message += "\n        (This will often be lagging as GP numbers come in at odd times)\n"

        # Depending on available data attempt to date stamp the data in the below format
        # 2021-09-01 Report date, using covidlive.com.au 
        # data published at: 2021-09-01 11:52:25 AEST
        if code_data["REPORT_DATE"] is not None and code_data["LAST_UPDATED_DATE"]:
            message += f":robot_face: {code_data['REPORT_DATE']} Report, using covidlive.com.au\n        Data published at: {code_data['LAST_UPDATED_DATE']} AEST"

        return message
