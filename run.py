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


def startAdmin():
    # Code for process 3 (Admin Dashboard)
    print("Process 3 (Admin Dashboard) is running.")
    from app.admin import run_admin_server
    run_admin_server()


if __name__ == '__main__':
    # Ensure database is initialized before processes spawn
    init_db()

    p1 = multiprocessing.Process(target=startJarvis)
    p2 = multiprocessing.Process(target=listenHotword)
    p3 = multiprocessing.Process(target=startAdmin)
    p2.daemon = True
    p3.daemon = True
    p1.start()
    p2.start()
    p3.start()

    try:
        p1.join()
    except KeyboardInterrupt:
        print("\nShutdown requested by user...")
    finally:
        if p3.is_alive():
            p3.terminate()
            p3.join(timeout=2)
            if p3.is_alive():
                p3.kill()
        if p2.is_alive():
            p2.terminate()
            p2.join(timeout=2)
            if p2.is_alive():
                p2.kill()
        if p1.is_alive():
            p1.terminate()
            p1.join(timeout=2)
            if p1.is_alive():
                p1.kill()
        print("system stop")