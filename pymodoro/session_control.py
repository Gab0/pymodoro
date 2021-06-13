from typing import List, Optional
import os
import datetime
import sys
import random
import string
from . import configuration

DATE_FORMAT: str = "%H:%M:%S"


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
            f.write(self.CREATION_DATE.strftime(DATE_FORMAT) + "\n")
            f.write(f"{self.WORK} {self.REST}\n")
            for e in self.Events:
                f.write(datetime.strftime(e, self.DATE_FORMAT) + "\n")

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
            self.CREATION_DATE = datetime.datetime.strptime(content.strip("\n"), DATE_FORMAT)

            content = f.readline()
            self.WORK, self.REST = list(map(int, content.split(" ")))

            self.Events = []
            for event in f.readlines():
                try:
                    e = datetime.datetime.strptime(
                        event.strip("\n"),
                        DATE_FORMAT
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


def log(log_path: str, message):
    with open(log_path, 'a') as f:
        now = datetime.datetime.now()
        now_str = now.strftime("%d/%m - %H:%M:%S")
        f.write(f"[{now_str}] {message}\n")


def main():
    Action = sys.argv.pop(1)
    config = configuration.Config()

    session_exists = os.path.isfile(config.session_file)

    if Action == "create":
        if session_exists:
            os.remove(config.session_file)
        new_session = Session(config.session_file)
        new_session.write_session_file()

        log(config.log_path, "New session.")

    elif Action == "pause":
        if not session_exists:
            return
        with open(config.session_file, 'a') as f:
            now = datetime.datetime.now()
            f.write(now.strftime(DATE_FORMAT) + "\n")

    elif Action == "delete":
        os.remove(config.session_file)
        log(config.log_path, "Session aborted.")


if __name__ == '__main__':
    main()
