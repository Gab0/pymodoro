#!/bin/python

import random
import sys
import subprocess
import os
from functools import partial
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton,
                               QVBoxLayout, QWidget)
from __feature__ import snake_case, true_property

import yaml


def launch(identifier):
    print(identifier)
    subprocess.call(["pymodoro_ctrl", "create", identifier])
    sys.exit(0)


class Pane(QWidget):
    def __init__(self, actions_filepath):
        QWidget.__init__(self)

        self.layout = QVBoxLayout(self)

        self.buttons = []

        with open(actions_filepath) as f:
            identifiers = yaml.load(f.read(), yaml.loader.Loader)

        for category in identifiers:

            self.message = QLabel(category.upper())
            self.message.adjust_size()
            self.message.alignment = Qt.AlignCenter
            self.layout.add_widget(self.message)
            for identifier in identifiers[category]:
                button = QPushButton(identifier)
                button.clicked.connect(partial(launch, identifier))
                self.buttons.append(button)
                self.layout.add_widget(button)

        for _ in range(5):
            self.layout.add_widget(QLabel(""))

    @Slot()
    def magic(self):
        self.message.text = random.choice(self.hello)


def main():
    app = QApplication(sys.argv)

    widget = Pane(os.path.join(os.getenv("HOME"), ".pomodoro_actions"))
    widget.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
