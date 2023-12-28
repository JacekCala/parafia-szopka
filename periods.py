import datetime as dt
import glob
import os


class Period:

    def __init__(self, name=None, start_date=None, end_date=None, mp3_files=None, folder=None):

        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.mp3_files = mp3_files
        self.folder = folder

    def __str__(self) -> str:
        return f'{{name = {self.name}, start_date = {self.start_date}, end_date = {self.end_date}, folder = {self.folder}, mp3_files = {self.mp3_files}}}'

    def __repr__(self) -> str:
        return f'Period("{self.name}", {self.start_date}, {self.end_date}, {self.mp3_files}, {"\"" + self.folder + "\"" if self.folder else None})'



def find_period(periods: list, cur_date, hint=None):
    """Find the first period on the list which includes the given cur_date. If hint is provided, first check if the hint fits the condition."""

    if hint:
        if cur_date >= hint.start_date and cur_date <= hint.end_date:
            return hint

    for p in periods:
        if cur_date >= p.start_date and cur_date <= p.end_date:
            return p
    
    return None


def read_periods(config: dict, data_root='.') -> list:
    start_date = dt.datetime.strptime(config['start-date'], "%Y-%m-%d")

    periods = []
    for p in config['periods']:
        end_date = dt.datetime.strptime(p['end-date'], '%Y-%m-%d')
        end_date = dt.datetime(end_date.year + start_date.year - 1, end_date.month, end_date.day)
        folder = os.path.join(data_root, p.get('folder', '.'))
        periods.append(Period(name=p['name'], end_date=end_date, mp3_files=glob.glob(folder  + '/*.mp3'), folder=folder))

    periods.sort(key=lambda x: x.end_date)
    sd = start_date
    for p in periods:
        p.start_date = sd
        sd = p.end_date

    return periods
