from typing import Any, List, Optional
import argparse
import re
import os
import datetime
import sys
import random
import string

import numpy as np
import matplotlib.pyplot as plt
from . import configuration

DATE_FORMAT: str = "%H:%M:%S"
DATE_FORMAT_LOG: str = "%d/%m/%y - %H:%M:%S"
DATE_FORMAT_SHOW: str = "%d/%m/%y - %A - %H:%M:%S"


def parse_arguments():
    parser = argparse.ArgumentParser()

    actions = parser.add_subparsers(title="check", dest="action")

    create = actions.add_parser("create")
    create.add_argument(dest="identifier")

    check = actions.add_parser("check")

    _pause = actions.add_parser("pause")
    _plot = actions.add_parser("plot")
    _autofill = actions.add_parser("autofill")
    _delete = actions.add_parser("delete")

    check.add_argument(
        "-d",
        "--past-days",
        type=int,
        help="Days back to search for.",
        default=30
    )

    check.add_argument(dest="queries", nargs="*")
    return parser.parse_args()


class Session():
    Events: List[datetime.datetime] = []
    WORK: int = 25
    REST: int = 5
    ID: str = ""
    CREATION_DATE: datetime.datetime = datetime.datetime.now()
    LAST_CHECK: Optional[datetime.datetime] = None
    REMAINING_SEC: int = 0

    def __init__(self, filepath):
        self.ID = self.generate_id()
        self.filepath = filepath
        self.read_session_file()

    def write_session_file(self):
        with open(self.filepath, 'w') as f:
            f.write(self.ID + "\n")
            f.write(self.CREATION_DATE.strftime(DATE_FORMAT_LOG) + "\n")
            f.write(f"{self.WORK} {self.REST}\n")
            for e in self.Events:
                f.write(datetime.datetime.strftime(e, DATE_FORMAT_LOG) + "\n")

    @property
    def is_paused(self) -> bool:
        print(self.Events)
        if len(self.Events) % 2:
            print(True)
            return True
        return False

    def read_session_file(self):
        """Get pomodoro and break durations from session as a list."""
        self.LAST_CHECK = datetime.datetime.now()
        if not os.path.exists(self.filepath):
            return

        with open(self.filepath) as f:
            content = f.readline()
            self.ID = content

            content = f.readline()
            self.CREATION_DATE = datetime.datetime.strptime(
                content.strip("\n"),
                DATE_FORMAT_LOG
            )

            content = f.readline()
            self.WORK, self.REST = list(map(int, content.split(" ")))

            self.Events = []
            for event in f.readlines():
                try:
                    e = datetime.datetime.strptime(
                        event.strip("\n"),
                        DATE_FORMAT_LOG
                    )
                    self.Events.append(e)
                except ValueError:
                    print(event)
                    raise
    @staticmethod
    def generate_id() -> str:
        chars = string.ascii_uppercase + string.digits
        return "".join([random.choice(chars) for _ in range(6)])

    def read_session_creation_time(self) -> Optional[datetime.datetime]:
        if os.path.exists(self.filepath):
            creation_timestamp = os.path.getctime(self.filepath)
            creation_time = datetime.datetime.fromtimestamp(creation_timestamp)
            return creation_time

        return None

    def get_seconds_left(self) -> Optional[int]:
        """Return seconds remaining in the current session."""
        seconds_left = None

        session_duration = self.WORK * 60

        session_creation_time = self.CREATION_DATE

        now = datetime.datetime.now()

        if os.path.isfile(self.filepath):
            delta_creation = (now - session_creation_time).seconds

            if self.LAST_CHECK is not None:
                delta_check_sec = (session_creation_time - self.LAST_CHECK).seconds

                if delta_check_sec > 5:
                    # the session file has been updated
                    # re-read the contents
                    self.read_session_file()

            seconds_left = session_duration - delta_creation

            paused_seconds = 0
            for i, event in enumerate(self.Events):
                if i % 2:
                    d = (event - self.Events[i-1]).seconds
                    print(">" + str(d))
                    paused_seconds += d

            frozen = 0
            if self.is_paused:
                frozen = (now - self.Events[-1]).seconds

            return seconds_left + paused_seconds + frozen

        return None


def log(log_path: str, message, date=datetime.datetime.now()):
    with open(log_path, 'a') as f:

        now_str = date.strftime(DATE_FORMAT_LOG)
        f.write(f"[{now_str}] {message}\n")


def check_entries(config, past_days=7, identifier: str = "research", Verbose: int = 1) -> List[List[datetime.datetime]]:
    now = datetime.datetime.now()
    Dates = []
    with open(config.log_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            res = re.findall(rf"\[([\d -:]+)\] {identifier} session.", line)
            if res:
                date = datetime.datetime.strptime(res[0], DATE_FORMAT_LOG)
                Dates.append(date)

    preliminary = [
        abs((now - date).total_seconds())
        for date in Dates
        if abs((now - date).total_seconds()) < past_days * 24 * 3600
    ]

    Results = []
    for day in range(past_days, -1, -1):
        moment = now - datetime.timedelta(hours=24*day)
        res = check_entries_day(Dates, moment, Verbose)
        Results.append(res)

    n_expected = len(preliminary)
    n_results = sum(len(r) for r in Results)
    if n_expected != n_results:
        print(f"Bad calculation! Expected {n_expected} but got {n_results}.")

    return Results


def same_day(dates=List[datetime.datetime]) -> bool:
    return len(list(set([(d.day, d.month, d.year) for d in dates]))) == 1


def check_entries_day(Dates: List[datetime.datetime], moment: datetime.datetime, Verbose: int = 1) -> List[datetime.datetime]:

    INTERVAL_MIN = 20
    HOUR_LIMIT = 7

    CurrentDates = []
    for d, date in enumerate(Dates):
        if d:
            OLD = abs((date - Dates[d - 1]).total_seconds()) / 60 > INTERVAL_MIN

            if not OLD:
                continue

        shifted = date - datetime.timedelta(hours=HOUR_LIMIT)

        if shifted.date() == moment.date():
            CurrentDates.append(date)

    Count = len(CurrentDates)
    if Verbose:
        print(f"Summary for {moment.strftime(DATE_FORMAT_SHOW)}.")
        print(f"Pomodoro sessions completed sucessfully: {Count}")
        print()

    return CurrentDates


def plot_days(config):

    days = check_entries(config, Verbose=2)

    matrix = np.zeros(shape=(len(days), 24 * 6))
    for d, day in enumerate(days):
        for date in day:
            start = date.hour * 6 + round(date.minute / 10)
            end = start + 3
            matrix[d, start:end] = 1

    plt.matshow(matrix)
    locs, labels = plt.xticks()

    def to_time(x):
        H = x // 6
        M = x % 6 * 10
        return f"%.2i:%.2i" % (H, M)

    new_ticks = map(to_time, locs)
    plt.xticks(ticks=locs, labels=new_ticks)

    plt.show()


def autofill(config, start_time, identifier, n):

    H = int(start_time[:2])
    M = int(start_time[2:])
    start_date = datetime.datetime.now().replace(
        hour=H, minute=M, second=0)

    for _ in range(n):
        log(config.log_path, f"{identifier} session.", start_date)
        start_date += datetime.timedelta(minutes=30)


def main():

    options = parse_arguments()

    Identifier = "research"
    if len(sys.argv) > 1:
        if not sys.argv[1].startswith("-"):
            Identifier = sys.argv.pop(1)

    config = configuration.Config(args=False)

    session_exists = os.path.isfile(config.session_file)

    if options.action == "create":
        if session_exists:
            session = Session(config.session_file)
            if session.get_seconds_left() > 0:
                return
            os.remove(config.session_file)

        new_session = Session(config.session_file)
        new_session.write_session_file()

        log(config.log_path, f"{options.identifier} session.")

    elif options.action == "pause":
        if not session_exists:
            return
        with open(config.session_file, 'a', encoding="utf-8") as f:
            now = datetime.datetime.now()
            f.write(now.strftime(DATE_FORMAT_LOG) + "\n")

    elif options.action == "delete":
        os.remove(config.session_file)
        log(config.log_path, "Session aborted.")

    elif options.action == "check":
        for Identifier in options.queries:
            total = check_entries(config, options.past_days, identifier=Identifier)
            ts = [len(x) for x in total]
            print(f"Total: {sum(ts)}")

    elif options.action == "plot":
        plot_days(config)

    elif options.action == "autofill":
        try:
            start_time = sys.argv[1]
            number = sys.argv[2]
        except IndexError:
            print("Wrong arguments for autofill (sample args: research 1700 2).")
            sys.exit(1)

        try:
            number = int(number)
        except:
            print("Bad 'number' argument.")
            sys.exit(1)

        autofill(config, start_time, Identifier, number)


if __name__ == '__main__':
    main()
