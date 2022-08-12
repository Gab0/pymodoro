import os
from argparse import ArgumentParser

import configparser


class Config(object):
    """Load config from defaults, file and arguments."""

    def __init__(self):

        self.load_defaults()
        self.load_user_data()
        self.load_from_file()
        self.load_from_args()

    def load_defaults(self):

        # File paths
        self.script_path = self._get_script_path()
        self.data_path = os.path.join(self.script_path, 'data')
        self.session_file = os.path.expanduser('~/.pomodoro_session')
        self.auto_hide = False

        self.log_path = os.path.expanduser("~/.pomodoro_log")
        self.shortOutput = True

        # Cosmetics
        self.colorize_output = True
        self.progress_bar_size = 8

        # Times
        self.session_duration_in_minutes = 25
        self.session_duration_in_seconds = self.session_duration_in_minutes * 60 + 1
        self.break_duration_in_minutes = 5
        self.break_duration_in_seconds = self.break_duration_in_minutes * 60
        self.update_interval_in_seconds = 1

        # Progress Bar
        self.total_number_of_marks = self.session_duration_in_minutes
        self.session_full_mark_character = '#'
        self.break_full_mark_character = '|'
        self.empty_mark_character = '·'
        self.left_to_right = False

        # Prefixes
        self.break_prefix = 'B '
        self.break_suffix = ''
        self.pomodoro_prefix = 'P '
        self.pomodoro_suffix = ''

        # Sound
        self.enable_sound = True
        self.enable_tick_sound = False
        self.sound_command = 'aplay -q %s &'
        self.session_sound_file = os.path.join(self.data_path, 'clap.wav')
        self.break_sound_file = os.path.join(self.data_path, 'crash.wav')
        self.tick_sound_file = os.path.join(self.data_path, 'tick.wav')

        # Run until SIGINT or any other interrupts by default.
        self.enable_only_one_line = False

        # Files for hooks (TODO make configurable)
        self.start_pomodoro_hook_file = os.path.expanduser("~/.pymodoro/hooks/start-pomodoro.py")
        self.complete_pomodoro_hook_file = os.path.expanduser("~/.pymodoro/hooks/complete-pomodoro.py")

        self.Color = {
            "session": "ff1010",
            "paused": "a010a0",
            "break": "10ff10"
        }

    def load_user_data(self):
        """
        Custom User Data

        Check the ~/.local/share/pymodoro directory for custom user
        files. This lets the user provide their own sound files which
        are used instead of the default ones.

        """
        self._user_dir = os.path.expanduser('~/.local/share/pymodoro')

        if not os.path.exists(self._user_dir):
            os.makedirs(self._user_dir)

        # Include any custom user sounds if present
        user_session_sound = os.path.join(self._user_dir, 'breakbeat.wav')
        user_break_sound = os.path.join(self._user_dir, 'crash.wav')
        user_tick_sound = os.path.join(self._user_dir, 'clap.wav')

        if os.path.exists(user_session_sound):
            self.session_sound_file = user_session_sound
        if os.path.exists(user_break_sound):
            self.break_sound_file = user_break_sound
        if os.path.exists(user_tick_sound):
            self.tick_sound_file = user_tick_sound

    def load_from_file(self):
        # We need to set the default for oneline in the parser here so
        # that users migrating from an older version of pymodoro who
        # have an old config file that does not contain the oneline
        # option don't crash when the parser tries to read it.
        defaults = {'oneline': str(self.enable_only_one_line).lower()}
        self._parser = configparser.RawConfigParser(defaults)
        self._dir = os.path.expanduser('~/.config/pymodoro')
        self._file = os.path.join(self._dir, 'config')
        self._load_config_file()

    def _get_script_path(self):
        module_path = os.path.realpath(__file__)
        return os.path.dirname(module_path)

    def _load_config_file(self):
        if not os.path.exists(self._file):
            self._create_config_file()

        self._parser.read(self._file)

        try:
            self.session_file = self._config_get_quoted_string('General', 'session')
            self.auto_hide = self._parser.getboolean('General', 'autohide')
            # Set 'oneline' to True if you want pymodoro to output only one line and exit.
            self.enable_only_one_line = self._parser.getboolean('General', 'oneline')

            self.pomodoro_prefix = self._config_get_quoted_string('Labels', 'pomodoro_prefix')
            self.pomodoro_suffix = self._config_get_quoted_string('Labels', 'pomodoro_suffix')
            self.break_prefix = self._config_get_quoted_string('Labels', 'break_prefix')
            self.break_suffix = self._config_get_quoted_string('Labels', 'break_suffix')

            self.left_to_right = self._parser.getboolean('Progress Bar', 'left_to_right')
            self.total_number_of_marks = self._parser.getint('Progress Bar', 'total_marks')
            self.session_full_mark_character = self._config_get_quoted_string('Progress Bar', 'session_character')
            self.break_full_mark_character = self._config_get_quoted_string('Progress Bar', 'break_character')
            self.empty_mark_character = self._config_get_quoted_string('Progress Bar', 'empty_character')

            self.enable_sound = self._parser.getboolean('Sound', 'enable')
            self.enable_tick_sound = self._parser.getboolean('Sound', 'tick')
            self.sound_command = self._config_get_quoted_string('Sound', 'sound_command')
        except configparser.NoOptionError:
            # If the option is missing from the config file (old version of the file
            # for example), don't throw an exception, just use the defaults
            pass


    def _create_config_file(self):
        self._parser.add_section('General')
        self._parser.set('General', 'autohide', str(self.auto_hide).lower())
        self._config_set_quoted_string('General', 'session', self.session_file)
        self._parser.set('General', 'oneline', str(self.enable_only_one_line).lower())

        self._parser.add_section('Labels')
        self._config_set_quoted_string('Labels', 'pomodoro_prefix', self.pomodoro_prefix)
        self._config_set_quoted_string('Labels', 'pomodoro_suffix', self.pomodoro_suffix)
        self._config_set_quoted_string('Labels', 'break_prefix', self.break_prefix)
        self._config_set_quoted_string('Labels', 'break_suffix', self.break_suffix)

        self._parser.add_section('Progress Bar')
        self._parser.set('Progress Bar', 'left_to_right', str(self.left_to_right).lower())
        self._parser.set('Progress Bar', 'total_marks', self.total_number_of_marks)
        self._config_set_quoted_string('Progress Bar', 'session_character',
                                       self.session_full_mark_character)
        self._config_set_quoted_string('Progress Bar', 'break_character',
                                       self.break_full_mark_character)
        self._config_set_quoted_string('Progress Bar', 'empty_character',
                                       self.empty_mark_character)

        self._parser.add_section('Sound')
        self._parser.set('Sound', 'enable', str(self.enable_sound).lower())
        self._parser.set('Sound', 'tick', str(self.enable_tick_sound).lower())
        self._parser.set('Sound', 'command', str(self.sound_command).lower())

        if not os.path.exists(self._dir):
            os.makedirs(self._dir)

        with open(self._file, 'at') as configfile:
            self._parser.write(configfile)

    def _config_set_quoted_string(self, section, option, value):
        """
        Surround this string option in double quotes so whitespace can
        be included.
        """
        value = '"' + str(value) + '"'
        self._parser.set(section, option, value)

    def _config_get_quoted_string(self, section, option):
        """
        Remove doublequotes from a string option.
        """
        return self._parser.get(section, option).strip('"')

    def load_from_args(self):
        arg_parser = ArgumentParser(description='Create a Pomodoro display for a status bar.')

        arg_parser.add_argument('-s', '--seconds', action='store_true', help='Changes format of input times from minutes to seconds.', dest='durations_in_seconds')
        arg_parser.add_argument('session_duration', action='store', nargs='?', type=int, help='Pomodoro duration in minutes (default: 25).', metavar='POMODORO DURATION')
        arg_parser.add_argument('break_duration', action='store', nargs='?', type=int, help='Break duration in minutes (default: 5).', metavar='BREAK DURATION')

        arg_parser.add_argument('-f', '--file', action='store', help='Pomodoro session file (default: ~/.pomodoro_session).', metavar='PATH', dest='session_file')
        arg_parser.add_argument('-n', '--no-break', action='store_true', help='No break sound.', dest='no_break')
        arg_parser.add_argument('-ah', '--auto-hide', action='store_true', help='Hide output when session file is removed.', dest='auto_hide')

        arg_parser.add_argument('-i', '--interval', action='store', type=int, help='Update interval in seconds (default: 1).', metavar='DURATION', dest='update_interval_in_seconds')
        arg_parser.add_argument('-l', '--length', action='store', type=int, help='Bar length in characters (default: 10).', metavar='CHARACTERS', dest='total_number_of_marks')

        arg_parser.add_argument('-p', '--pomodoro', action='store', help='Pomodoro full mark characters (default: #).', metavar='CHARACTER', dest='session_full_mark_character')
        arg_parser.add_argument('-b', '--break', action='store', help='Break full mark characters (default: |).', metavar='CHARACTER', dest='break_full_mark_character')
        arg_parser.add_argument('-e', '--empty', action='store', help='Empty mark characters (default: ·).', metavar='CHARACTER', dest='empty_mark_character')

        arg_parser.add_argument('-sp', '--pomodoro-sound', action='store', help='Pomodoro end sound file (default: session.wav).', metavar='PATH', dest='session_sound_file')
        arg_parser.add_argument('-sb', '--break-sound', action='store', help='Break end sound file (default: break.wav).', metavar='PATH', dest='break_sound_file')
        arg_parser.add_argument('-st', '--tick-sound', action='store', help='Ticking sound file (default: tick.wav).', metavar='PATH', dest='tick_sound_file')
        arg_parser.add_argument('-si', '--silent', action='store_true', help='Play no end sounds', dest='silent')
        arg_parser.add_argument('-t', '--tick', action='store_true', help='Play tick sound at every interval', dest='tick')
        arg_parser.add_argument('-sc', '--sound-command', action='store', help='Command callled to play a sound. Default to "aplay -q %%s &". %%s will be replaced with the sound filename.', metavar='SOUND COMMAND', dest='sound_command')
        arg_parser.add_argument('-ltr', '--left-to-right', action='store_true', help='Display markers from left to right (incrementing marker instead of decrementing)', dest='left_to_right')
        arg_parser.add_argument('-bp', '--break-prefix', action='store', help='String to display before, when we are in a break. Default to "B". Can be used to format display for dzen.', metavar='BREAK PREFIX', dest='break_prefix')
        arg_parser.add_argument('-bs', '--break-suffix', action='store', help='String to display after, when we are in a break. Default to "". Can be used to format display for dzen.', metavar='BREAK SUFFIX', dest='break_suffix')
        arg_parser.add_argument('-pp', '--pomodoro-prefix', action='store', help='String to display before, when we are in a pomodoro. Default to "P". Can be used to format display for dzen.', metavar='POMODORO PREFIX', dest='pomodoro_prefix')
        arg_parser.add_argument('-ps', '--pomodoro-suffix', action='store', help='String to display after, when we are in a pomodoro. Default to "". Can be used to format display for dzen.', metavar='POMODORO SUFFIX', dest='pomodoro_suffix')

        arg_parser.add_argument('-o', '--one-line', action='store_true', help='Print one line of output and quit.', dest='oneline')

        arg_parser.add_argument('-onc', action='store_true', dest='shortOutput')
        args = arg_parser.parse_args()

        if args.session_duration:
            if args.durations_in_seconds:
                self.session_duration_in_seconds = args.session_duration
            else:
                self.session_duration_in_seconds = args.session_duration * 60
        if args.break_duration:
            if args.durations_in_seconds:
                self.break_duration_in_seconds = args.break_duration
            else:
                self.break_duration_in_seconds = args.break_duration * 60
        if args.update_interval_in_seconds:
            self.update_interval_in_seconds = args.update_interval_in_seconds
        if args.total_number_of_marks:
            self.total_number_of_marks = args.total_number_of_marks
        if args.session_full_mark_character:
            self.session_full_mark_character = args.session_full_mark_character
        if args.break_full_mark_character:
            self.break_full_mark_character = args.break_full_mark_character
        if args.empty_mark_character:
            self.empty_mark_character = args.empty_mark_character
        if args.session_file:
            self.session_file = args.session_file
        if args.session_sound_file:
            self.session_sound_file = args.session_sound_file
        if args.break_sound_file:
            self.break_sound_file = args.break_sound_file
        if args.tick_sound_file:
            self.tick_sound_file = args.tick_sound_file
        if args.silent:
            self.enable_sound = False
        if args.tick:
            self.enable_tick_sound = True
        if args.sound_command:
            self.sound_command = args.sound_command
        if args.left_to_right:
            self.left_to_right = True
        if args.no_break:
            self.break_duration_in_seconds = 0
        if args.auto_hide:
            self.auto_hide = True
        if args.break_prefix:
            self.break_prefix = args.break_prefix
        if args.break_suffix:
            self.break_suffix = args.break_suffix
        if args.pomodoro_prefix:
            self.pomodoro_prefix = args.pomodoro_prefix
        if args.pomodoro_suffix:
            self.pomodoro_suffix = args.pomodoro_suffix

        self.shortOutput = args.shortOutput

        if args.oneline:
            self.enable_only_one_line = True

