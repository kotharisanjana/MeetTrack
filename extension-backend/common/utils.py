import common.globals as global_vars
from __init__ import logger

from datetime import datetime, date
import os
import shutil

def get_unixtime(hour=0, minute=0, second=0, millisecond=0):
    """
    Get the Unix timestamp for a given time.
    
    :param hour: Hour of the day
    :param minute: Minute of the hour
    :param second: Second of the minute
    :param millisecond: Millisecond of the second
    :return: Unix timestamp
    """
    current_time = datetime.now()
    timestamp = datetime(current_time.year, current_time.month, current_time.day, hour, minute, second, millisecond*1000)
    unixtime = timestamp.timestamp()
    return unixtime


def get_date():
    """
    Get the current date.

    :return: Current date in the format YYYY-MM-DD
    """
    return date.today()


def delete_files(meeting_id):
    """
    Delete files from local file system after meeting ends

    :param meeting_id: ID of the meeting
    """
    directory_path = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}")
    shutil.rmtree(directory_path)