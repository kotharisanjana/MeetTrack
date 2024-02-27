from datetime import datetime

class Time:
    def __init__(self):
        self.year = datetime.now().year
        self.month = datetime.now().month
        self.day = datetime.now().day

    def get_time(self, hour=0, minute=0, second=0, millisecond=0):
        timestamp = datetime(self.year, self.month, self.day, hour, minute, second, millisecond*1000)
        unixtime = timestamp.timestamp()
        return unixtime