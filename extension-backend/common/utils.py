import common.globals as global_vars
from datetime import datetime, date
import os

def get_unixtime(hour=0, minute=0, second=0, millisecond=0):
    timestamp = datetime(datetime.now().year, datetime.now().month, datetime.now().day, hour, minute, second, millisecond*1000)
    unixtime = timestamp.timestamp()
    return unixtime

def get_date():
    return date.today()

def delete_files(meeting_id):
    for filename in os.listdir(global_vars.DOWNLOAD_DIR):
        if filename.startswith(str(meeting_id)):
            file_path = os.path.join(global_vars.DOWNLOAD_DIR, filename)
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")