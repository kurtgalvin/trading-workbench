import pandas as pd


class Strategy:
    def __init__(self, data):
        self.df = pd.DataFrame(data)

    def __init_subclass__(self):
        pass


class Indicator:
    pass