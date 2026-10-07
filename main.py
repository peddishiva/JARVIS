import os
import sys

import eel

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import init_db
from engine.command import *
from engine.features import *


def start():
    init_db()
    www_dir = os.path.join(BASE_DIR, "www")
    eel.init(www_dir)
    playAssistantSound()

    os.system('start msedge.exe --app="http://localhost:8000/index.html"')
    eel.start('index.html', mode=None, host="localhost", block=True)


if __name__ == '__main__':
    start()