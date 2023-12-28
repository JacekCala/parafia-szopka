import datetime as dt
import io
import json
import time
import threading


class MotionReader(io.TextIOBase):

    def __init__(self, file_name, break_event = None):
        self.file_name = file_name
        self.file = open(file_name, 'rb')
        self.start_time_ms = dt.datetime.now()
        if break_event:
            self.break_event = break_event
        else:
            self.break_event = threading.Event()

    
    def __enter__(self):
        return self


    def __exit__(self, *exc_details):
        if self.file:
            self.file.close()


    def readline(self, size: int = -1) -> str:
        data = self.file.readline(size)
        if data:
            str_data = data.decode('utf8')
            json_data = json.loads(str_data)
            while not self.break_event.is_set() and dt.datetime.now() < self.start_time_ms + dt.timedelta(milliseconds=json_data['timestamp']):
                time.sleep(0.1)

        return data