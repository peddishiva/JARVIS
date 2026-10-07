import os
import webbrowser

from app.config import ASSISTANT_NAME
from app.database import get_connection


def open_command(query, speak_fn=None, db_path=None):
    """Open a system application or web URL shortcut matching the query."""
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "")

    app_name = query.strip()

    if app_name != "":
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT path FROM sys_command WHERE name IN (?)", (app_name,)
            )
            results = cursor.fetchall()

            if len(results) != 0:
                if speak_fn:
                    speak_fn("Opening " + query)
                os.startfile(results[0][0])

            elif len(results) == 0:
                cursor.execute(
                    "SELECT url FROM web_command WHERE name IN (?)", (app_name,)
                )
                results = cursor.fetchall()

                if len(results) != 0:
                    if speak_fn:
                        speak_fn("Opening " + query)
                    webbrowser.open(results[0][0])

                else:
                    if speak_fn:
                        speak_fn("Opening " + query)
                    try:
                        os.system("start " + query)
                    except Exception:
                        if speak_fn:
                            speak_fn("not found")
        except Exception:
            if speak_fn:
                speak_fn("something went wrong")
        finally:
            conn.close()
