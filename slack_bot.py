from ssl import SSLContext
from typing import List, Dict
from datetime import timedelta, date, datetime
import math

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

    def post_messages_to_slack(self, blocks) -> SlackResponse:
        print("Posting stats to slack")
        return self.client.chat_postMessage(
            channel=self.channel_name,
            text="COVID stats updated",
            username=self.bot_name,
            icon_emoji=self.emoji,
            blocks=blocks
        )

    # For the filtered data, generate messages and send them to slack
    def execute_for_covid_data(self, covid_data: Dict) -> SlackResponse:
        # Generate the messages for each state/country code
        messages: List[str] = []
        for code_data in covid_data:
            messages.append(self.generate_message_for_code(covid_data[code_data]))

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            } for message in messages
        ]

        # Post these messages to slack
        return self.post_messages_to_slack(blocks)

    def execute_for_vax_stats(self, vax_data: Dict) -> SlackResponse:
        # Generate the messages for each state/country code
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":dart: Vax Stats"
                }
            },
            {
                "type": "divider"
            }
        ] 
        
        for block in (self.generate_vax_stats_for_code(vax_data[code]) for code in vax_data):
            blocks.extend(block)

        # Post these messages to slack
        return self.post_messages_to_slack(blocks)

    def generate_vax_stats_for_code(self, vax_data: Dict) -> List:
        # generate vax stats for each state/country code
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":{vax_data['CODE_EMOJI']}:    *{vax_data['CODE']}*\n"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{int(vax_data['VACC_DOSE_CNT']):,d}* total doses administered. Data published at {vax_data['LAST_UPDATED_DATE']} AEST"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": 
                        f"\n  :syringe: *1st dose* ({vax_data['POPULATION_BRACKET']})"
                        f"\n    {self.format_vax_stat(0.6, vax_data, 'VACC_FIRST_DOSE_CNT')}"
                        f"\n    {self.format_vax_stat(0.7, vax_data, 'VACC_FIRST_DOSE_CNT')}"
                        f"\n    {self.format_vax_stat(0.8, vax_data, 'VACC_FIRST_DOSE_CNT')}"
                        f"\n    {self.format_vax_stat(0.9, vax_data, 'VACC_FIRST_DOSE_CNT')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": 
                        f"\n  :syringe::syringe: *2nd dose* ({vax_data['POPULATION_BRACKET']})"
                        f"\n    {self.format_vax_stat(0.6, vax_data, 'VACC_PEOPLE_CNT')}"
                        f"\n    {self.format_vax_stat(0.7, vax_data, 'VACC_PEOPLE_CNT')}"
                        f"\n    {self.format_vax_stat(0.8, vax_data, 'VACC_PEOPLE_CNT')}"
                        f"\n    {self.format_vax_stat(0.9, vax_data, 'VACC_PEOPLE_CNT')}"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]

    def format_vax_stat(self, target_percentage: float, vax_data: Dict, vax_field: str) -> str:
        vax_percentage: float = self.vax_to_percentage(vax_data, vax_field)
        vax_status: str = ":white_check_mark:"

        if vax_percentage < target_percentage:
            rolling_avg = (vax_percentage - self.vax_to_percentage(vax_data, "PREV_" + vax_field)) / vax_data["RECORD_COUNT"] 

            days_to_target = math.ceil((target_percentage - vax_percentage) / rolling_avg)
            
            if days_to_target > 365:
                vax_status = ":no_entry:"
            else:
                dt = datetime.strptime(vax_data["LAST_UPDATED_DATE"], "%Y-%m-%d %H:%M:%S") + timedelta(days=days_to_target)
                vax_status = dt.strftime("%b %d")
        
        #example format: *60%* Oct 10
        return f"*{target_percentage:.0%}:* {vax_status}"

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
        # 12,046 New doses | 466,621 total | 78.2% (+0.2) 1st dose | 42.2% (+0.01) 2nd dose
        # (This will often be incorrect as GP numbers come in at odd times)
        if new_vax is not None:
            message += f":syringe: {int(code_data['VACC_DOSE_CNT']):,d} doses (+{new_vax:,d})"

            if code_data["VACC_FIRST_DOSE_CNT"] is not None and code_data["VACC_FIRST_DOSE_CNT"] != 0:
                message += self.format_vax(code_data, "VACC_FIRST_DOSE_CNT", "1st")

            if code_data["VACC_PEOPLE_CNT"] is not None and code_data["VACC_PEOPLE_CNT"] != 0:
                message += self.format_vax(code_data, "VACC_PEOPLE_CNT", "2nd")

            message += "\n        (This will often be lagging as GP numbers come in at odd times)\n"

        # Depending on available data attempt to date stamp the data in the below format
        # 2021-09-01 Report date, using covidlive.com.au 
        # data published at: 2021-09-01 11:52:25 AEST
        if code_data["REPORT_DATE"] is not None and code_data["LAST_UPDATED_DATE"]:
            message += f":robot_face: {code_data['REPORT_DATE']} Report, using covidlive.com.au\n        Data published at: {code_data['LAST_UPDATED_DATE']} AEST"

        return message

    def format_vax(self, code_data: Dict, vax_field: str, ordinal: str) -> str:
        current_dose = self.vax_to_percentage(code_data, vax_field)
        prev_dose = self.vax_to_percentage(code_data, 'PREV_' + vax_field)
        dose_delta = current_dose - prev_dose
        return f" | {current_dose:.1%} (+{dose_delta*100:.2}) {code_data['POPULATION_BRACKET']} {ordinal} dose"

    def vax_to_percentage(self, code_data: Dict, vax_field: str) -> float:
        return int(code_data[vax_field])/int(code_data['POPULATION']);

