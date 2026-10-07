import multiprocessing
import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import init_db


def startJarvis():
    # Code for process 1
    print("Process 1 is running.")
    from main import start
    start()


def listenHotword():
    # Code for process 2
    print("Process 2 is running.")
    from engine.features import hotword
    hotword()


if __name__ == '__main__':
    # Ensure database is initialized before processes spawn
    init_db()

    p1 = multiprocessing.Process(target=startJarvis)
    p2 = multiprocessing.Process(target=listenHotword)
    p1.start()
    p2.start()

    try:
        p1.join()
    except KeyboardInterrupt:
        print("\nShutdown requested by user...")
    finally:
        if p2.is_alive():
            p2.terminate()
            p2.join()
        if p1.is_alive():
            p1.terminate()
            p1.join()
        print("system stop")