#!/bin/python
# -*- coding: utf-8 -*-
# authors: Dat Chu <dattanchu@gmail.com>
#          Dominik Mayer <dominik.mayer@gmail.com>
# Prerequisite
#  - aplay to play a sound of your choice
from typing import List

import os
import sys
import time
import subprocess

from subprocess import Popen

from . import configuration, session_control, color_gradient


class Pymodoro(object):

    IDLE_STATE = 'IDLE'
    ACTIVE_STATE = 'ACTIVE'
    BREAK_STATE = 'BREAK'
    WAIT_STATE = 'WAIT'
    PAUSED_STATE = 'PAUSED'

    last_progress = ""

    def __init__(self):
        self.config = configuration.Config()
        self.session_file = os.path.expanduser(self.config.session_file)

        self.session = session_control.Session(self.session_file)
        self.set_durations(self.session)
        self.running = True

        # cache last time the session file was touched
        # to know if the session file contents should be re-read
        self.last_start_time = 0

    def run(self):
        """ Start main loop."""
        while self.running:
            self.update_state()
            self.print_output()
            self.tick_sound()
            if self.config.enable_only_one_line:
                break
            else:
                self.wait()

    def update_state(self):
        """ Update the current state determined by timings."""
        if not hasattr(self, 'state'):
            self.state = self.IDLE_STATE

        seconds_left = self.session.get_seconds_left()
        break_duration = self.config.break_duration_in_seconds
        break_elapsed = self.get_break_elapsed(seconds_left)

        if self.session.is_paused:
            self.state = self.PAUSED_STATE
            return

        if seconds_left is None:
            self.state = self.IDLE_STATE
        elif seconds_left >= 0:
            self.state = self.ACTIVE_STATE
        elif break_elapsed <= break_duration:
            self.state = self.BREAK_STATE
        else:
            self.state = self.WAIT_STATE

        current_state = self.state

        if seconds_left is None:
            next_state = self.IDLE_STATE
        elif seconds_left > 1:
            next_state = self.ACTIVE_STATE
        elif break_elapsed + 1 < break_duration or seconds_left == 1:
            next_state = self.BREAK_STATE
        else:
            next_state = self.WAIT_STATE

        if next_state is not current_state:
            self.send_notifications(next_state)

            # Execute hooks
            if all([
                    current_state == self.ACTIVE_STATE,
                    next_state == self.BREAK_STATE,
                    os.path.exists(self.config.complete_pomodoro_hook_file)
            ]):
                subprocess.check_call(self.config.complete_pomodoro_hook_file)

            elif (current_state != self.ACTIVE_STATE and
                  next_state == self.ACTIVE_STATE and
                  os.path.exists(self.config.start_pomodoro_hook_file)):
                subprocess.check_call(self.config.start_pomodoro_hook_file)

            self.state = next_state

    def send_notifications(self, next_state):
        """Send appropriate notifications when leaving a state."""
        current_state = self.state
        notification = None
        sound = None

        if current_state == self.ACTIVE_STATE:
            if next_state == self.BREAK_STATE:
                sound = self.config.session_sound_file
                notification = ["Worked enough.", "Time for a break!"]

        if current_state == self.BREAK_STATE:
            if next_state == self.WAIT_STATE:
                sound = self.config.break_sound_file
                notification = ["Break is over.", "Back to work!"]

        if notification:
            self.notify(notification)

        if sound:
            self.play_sound(sound)

    def make_output(self):
        """Make output determined by the current state."""
        auto_hide = self.config.auto_hide
        seconds_left = self.session.get_seconds_left()

        progress = ""
        timer = ""

        displayMethods = {
            True: self.get_colored_char,
            False: self.get_progress_bar
        }

        displayMethod = displayMethods[self.config.shortOutput]

        Color = "ffffff"

        if self.state == self.IDLE_STATE and not auto_hide:
            progress = ""

        elif self.state == self.ACTIVE_STATE:
            duration = self.config.session_duration_in_seconds
            output_seconds = self.get_output_seconds(seconds_left)
            output_minutes = self.get_minutes(seconds_left)

            progress = displayMethod(duration, seconds_left)
            timer = "%02d:%02d" % (output_minutes, output_seconds)
            Color = self.config.Color["session"]

        elif self.state == self.BREAK_STATE:
            duration = self.config.break_duration_in_seconds
            break_seconds = self.get_break_seconds_left(seconds_left)
            output_seconds = self.get_output_seconds(break_seconds)
            output_minutes = self.get_minutes(break_seconds)

            progress = displayMethod(duration, break_seconds)
            timer = "%02d:%02d" % (output_minutes, output_seconds)

            Color = self.config.Color["break"]

        elif self.state == self.WAIT_STATE:
            seconds = -seconds_left
            minutes = self.get_minutes(seconds)
            hours = self.get_hours(seconds)
            days = self.get_days(seconds)

            output_seconds = self.get_output_seconds(seconds)
            output_minutes = self.get_output_minutes(seconds)
            output_hours = self.get_output_hours(seconds)

            if minutes < 60:
                timer = "%02d:%02d min" % (minutes, output_seconds)
            elif hours < 24:
                timer = "%02d:%02d h" % (hours, output_minutes)
            elif days <= 7:
                timer = "%02d:%02d d" % (days, output_hours)
            else:
                timer = "Over a week"

        elif self.state == self.PAUSED_STATE:
            progress = self.last_progress
            Color = self.config.Color["paused"]

        else:
            raise Exception("Unknown state.")

        if self.state != self.PAUSED_STATE:
            self.last_progress = progress

        if self.config.colorize_output:
            progress = self.show_colored(Color, progress)

        return progress + '\n'

    def print_output(self):
        sys.stdout.write(self.make_output())
        sys.stdout.flush()

    def wait(self):
        """Wait for the specified interval."""
        interval = self.config.update_interval_in_seconds
        time.sleep(interval)

    def tick_sound(self):
        """Play the Pomodoro tick sound if enabled."""
        enabled = self.config.enable_tick_sound
        if enabled and self.state == self.ACTIVE_STATE:
            self.play_sound(self.config.tick_sound_file)

    def get_break_elapsed(self, seconds_left):
        """Return the break elapsed in seconds"""
        break_elapsed = 0
        if seconds_left:
            break_elapsed = abs(seconds_left)
        return break_elapsed

    def set_durations(self, session: session_control.Session):
        """Set durations from session values if available."""
        session.read_session_file()

        self.set_session_duration(session.WORK)
        self.set_break_duration(session.REST)

    def set_session_duration(self, session_duration: int):
        if session_duration != -1:
            self.config.session_duration_in_seconds = session_duration * 60

    def convert_string_to_int(self, string):
        if not string.isdigit():
            return -1
        else:
            return int(string)

    def set_break_duration(self, break_duration: int):
        """Modify break duration."""

        if break_duration != -1:
            self.config.break_duration_in_seconds = break_duration * 60

    def get_break_seconds_left(self, seconds):
        return self.config.break_duration_in_seconds + seconds

    def get_colored_char(self, duration_in_seconds, seconds):
        timefraction = seconds / duration_in_seconds

        Color = color_gradient.colorRainbow(timefraction)

        char = "W" if duration_in_seconds > 700 else "B"
        return self.show_colored(Color, char)

    @staticmethod
    def show_colored(Color, content):
        try:
            color = '%s%s%s' % Color
        except TypeError:
            color = Color

        return f"<fc=#{color}>{content}</fc>"

    def get_progress_bar(self, duration_in_seconds, seconds):
        """Return progess bar using full and empty characters."""
        output = ""
        total_marks = self.config.progress_bar_size
        left_to_right = self.config.left_to_right

        full_mark_character = self.config.session_full_mark_character
        empty_mark_character = self.config.empty_mark_character
        upper_quarter_marker_character = '#'
        middle_mark_character = 'X'
        quarter_mark_character = 'x'

        if self.state == self.BREAK_STATE:
            full_mark_character = self.config.break_full_mark_character

        if total_marks:
            seconds_per_mark = (duration_in_seconds / total_marks)
            fine_grain_measure = seconds % seconds_per_mark

            number_of_full_marks = int(seconds // seconds_per_mark)

            if not fine_grain_measure:
                MM = empty_mark_character
            elif fine_grain_measure > seconds_per_mark / 2:
                MM = middle_mark_character
            else:
                MM = quarter_mark_character
            # Reverse the display order
            if left_to_right:
                number_of_full_marks = total_marks - number_of_full_marks

            number_of_empty_marks = total_marks - number_of_full_marks

            full_marks = full_mark_character * number_of_full_marks
            empty_marks = empty_mark_character * number_of_empty_marks
            output = full_marks + MM + empty_marks

        return output

    def get_days(self, seconds):
        """Convert seconds to days."""
        return int(seconds / 86400)

    def get_hours(self, seconds):
        """Convert seconds to hours."""
        return int(seconds / 3600)

    def get_minutes(self, seconds):
        """Convert seconds to minutes."""
        return int(seconds / 60)

    def get_output_hours(self, seconds):
        hours = self.get_hours(seconds)
        days = self.get_days(seconds)
        output_hours = int(hours - days * 24)
        return output_hours

    def get_output_minutes(self, seconds):
        hours = self.get_hours(seconds)
        minutes = self.get_minutes(seconds)
        output_minutes = int(minutes - hours * 60)
        return output_minutes

    def get_output_seconds(self, seconds):
        minutes = self.get_minutes(seconds)
        output_seconds = int(seconds - minutes * 60)
        return output_seconds

    def play_sound(self, sound_file):
        """Play specified sound file with aplay by default."""
        if self.config.enable_sound:
            with open(os.devnull, 'wb') as devnull:
                subprocess.check_call(
                    self.config.sound_command % sound_file,
                    stdout=devnull,
                    stderr=subprocess.STDOUT,
                    shell=True
                )

    def notify(self, strings):
        """ Send a desktop notification. """
        try:
            Popen(['notify-send'] + strings)
        except OSError:
            pass


def main():
    pymodoro = Pymodoro()
    pymodoro.run()


if __name__ == "__main__":
    main()
