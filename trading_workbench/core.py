import pandas as pd


class BackTest:
    def __init__(self, strategy, data):
        x = strategy(data)
        print(x.sma)
        print(x.sma.now)
        print(x.sma.prev)


class Strategy:
    def __init__(self, data):
        df = pd.DataFrame(data)

        largest_prev = 0
        for v in self._indicators.values():
            v.build(df)
            if v.prev_count > largest_prev:
                largest_prev = v.prev_count
        
        largest_valid = 0
        for i in df.iteritems():
            first = i[1].first_valid_index()
            if first > largest_valid:
                largest_valid = first

        first_index = largest_prev + largest_valid
        for v in self._indicators.values():
            v.index = first_index

    def open(self, long=False, short=False):
        if long:
            pass
        elif short:
            pass

    def close(self):
        pass

    def __init_subclass__(cls):
        indicators = {}
        for k, v in cls.__dict__.items():
            if isinstance(v, Indicator):
                indicators[k] = v
        setattr(cls, '_indicators', indicators)


class Indicator:
    def __init__(self, indicator, params=None, prev=1):
        self.indicator = indicator
        self.params = params
        self.prev_count = prev
        self._index = None
        self._result = None

    def build(self, df):
        self._result = self.indicator(df, *self.params)
        return self._result

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

    @property
    def now(self):
        return self._result.iloc[self._index]

    @property
    def prev(self):
        return self._result.iloc[self._index-self.prev_count:self._index].iloc[::-1]

    def __str__(self):
        return str(self._result)


def SMA(df, n):
    df['sma'] = df['close'].rolling(n).mean()
    return df['sma']

class TestStrategy(Strategy):
    sma = Indicator(SMA, params=(2,), prev=2)

    def open_trade(self):
        pass

    def close_trade(self):
        pass


if __name__ == '__main__':
    data = {
        'open': [1,2,3,4,3,2,1,2,3,4,3,2,1],
        'high': [2,3,4,5,4,3,2,3,4,5,4,3,2],
        'low': [1,2,3,4,3,2,1,2,3,4,3,2,1],
        'close': [1.5,2.5,3.5,4.5,3.5,2.5,1.5,2.5,3.5,4.5,3.5,2.5,1.5]
    }
    x = BackTest(TestStrategy, data)