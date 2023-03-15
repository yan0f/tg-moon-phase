import os
import pathlib
from datetime import datetime, timedelta

import pylunar
from crontab import CronTab
from dotenv import find_dotenv, load_dotenv
from pylunar import MoonInfo
from telethon.sync import TelegramClient
from telethon.tl.functions.account import UpdateEmojiStatusRequest
from telethon.types import EmojiStatus

load_dotenv(find_dotenv())

API_HASH = os.environ['API_HASH']
API_ID = int(os.environ['API_ID'])

SAINT_PETERSBURG_COORDINATES = (59, 56, 15), (30, 18, 30)


def next_moon_phase_datetime(moon_info: MoonInfo) -> datetime:
    next_phase_datetime = moon_info.next_four_phases()[0][1]
    next_moon_phase_date = datetime(*next_phase_datetime[:-1])  # UTC without seconds, since cron doesn't support them anyway
    timezone_offset = timedelta(hours=3)  # UTC -> UTC+3
    extra_minute = timedelta(minutes=1)  # moon phase won't change cuz we threw out the seconds, so we'll add extra min
    return next_moon_phase_date + timezone_offset + extra_minute


def get_tg_emoji_document_id(moon_info: MoonInfo) -> int:
    match moon_info.phase_name():
        case 'NEW_MOON':
            return 5188497854242495901  # 🌑
        case "WAXING_CRESCENT":
            return 5188666899860298925  # 🌒
        case 'FIRST_QUARTER':
            return 5190851612284819957  # 🌓
        case 'WAXING_GIBBOUS':
            return 5188461347020481276  # 🌔
        case 'FULL_MOON':
            return 5188608638628929611  # 🌕
        case 'WANING_GIBBOUS':
            return 5188452705546281155  # 🌖
        case 'LAST_QUARTER':
            return 5188420746694633417  # 🌗
        case 'WANING_CRESCENT':
            return 5188377234380954537  # 🌘


def set_status(document_id: int, session_file: str) -> None:
    with TelegramClient(session_file, API_ID, API_HASH) as client:
        client(UpdateEmojiStatusRequest(EmojiStatus(document_id)))


def set_cronjob(datetime_: datetime, command: str) -> None:
    with CronTab(user=True) as cron:
        job = cron.new(command)
        job.setall(datetime_)


def delete_previous_cronjobs(command: str) -> None:
    with CronTab(user=True) as cron:
        cron.remove_all(command=command)


if __name__ == '__main__':
    abspath = pathlib.Path(__file__).resolve()

    moon_info = pylunar.MoonInfo(*SAINT_PETERSBURG_COORDINATES)

    document_id = get_tg_emoji_document_id(moon_info)
    set_status(document_id, str(abspath.parent / 'anon.session'))

    next_moon_phase_datetime_ = next_moon_phase_datetime(moon_info)
    command = f'{abspath.parent}/venv/bin/python {abspath} >> out.txt  2>&1'

    delete_previous_cronjobs(command)
    set_cronjob(next_moon_phase_datetime_, command)
