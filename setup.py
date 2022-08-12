import os
import glob
from setuptools import setup, find_packages

datadir = 'data'
datafiles = [(datadir, [f for f in glob.glob(os.path.join(datadir, '*'))])]

setup(
    name='pymodoro',
    version='0.3',
    py_modules=['pymodoro', 'pymodoroi3', "color_gradient", "session_control"],
    packages=find_packages(),
    data_files=datafiles,
    entry_points={
        "console_scripts": [
            "pymodoro = pymodoro.pymodoro:main",
            "pymodoroi3 = pymodoro.pymodoroi3:main",
            "pymodoro_ctrl = pymodoro.session_control:main",
            "pymodoro_routine = pymodoro.routine_control:main",
            "pymodoro_signal = pymodoro.signal:main"
        ]
    },
)
