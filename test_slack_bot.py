import json
from typing import Dict

from slack_bot import CovidSlackBot


def test_generate_message_for_code():
    with open("resources/nsw.json") as file:
        nsw_data: Dict = json.load(file)

    slack_bot: CovidSlackBot = CovidSlackBot(
        "Fake Token Here",
        "Channel Name Here",
        "CovidLiveSummary",
        ":robot_face:",
    )

    message = slack_bot.generate_message_for_code(nsw_data)
    expected = """--- *Latest COVID figures for NSW* ---
:helmet_with_white_cross: 1,102 New total cases | 19,040 active cases (+1,041)
:earth_asia: 2 New overseas cases
:hospital: 908 (+39) Hospitalised | 150 (+7) in ICU | 66 (+8) ventilated
:skull: +4 Deaths | 154 Total COVID Deaths
:test_tube: +173,913 Tests in the last reporting period | 13,367,758 total tests
:syringe: 6,990,810 doses (+121,170) | 69.3% (+1.1) 16+ 1st dose | 37.8% (+0.77) 16+ 2nd dose
        (This will often be lagging as GP numbers come in at odd times)
:robot_face: 2021-09-01 Report, using covidlive.com.au
        Data published at: 2021-09-01 11:15:06 AEST"""

    assert message == expected, f"Message: message should match expected"
