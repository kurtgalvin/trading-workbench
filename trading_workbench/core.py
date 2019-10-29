import pandas as pd


class BackTest:
    def __init__(self, strategy, data):
        self.strategy = strategy(data)

    def run(self):
        for i in self.strategy:
            pass


class Strategy:
    def __init__(self, data):
        df = pd.DataFrame(data)

        largest_prev = 0
        for v in self._indicators.values():
            v.build(df, strategy=self)
            if v.prev_count > largest_prev:
                largest_prev = v.prev_count
        
        largest_valid = 0
        for i in df.iteritems():
            first = i[1].first_valid_index()
            if first > largest_valid:
                largest_valid = first

        self.index = largest_prev + largest_valid
        self.max_index = 10

    def trade(self, direction):
        if direction == 'long':
            pass
        elif direction == 'short':
            pass

    def __iter__(self):
        return self

    def __next__(self):
        if self.index <= self.max_index:
            print(self.index)
            self.index += 1
            return None
        raise StopIteration

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
        self._result = None

    def build(self, df, strategy=None):
        self._result = self.indicator(df, *self.params)
        if isinstance(strategy, Strategy):
            self._strategy = strategy
        return self._result

    @property
    def index(self):
        return self._strategy.index

    @property
    def now(self):
        return self._result.iloc[self.index]

    @property
    def prev(self):
        return self._result.iloc[self.index-self.prev_count:self.index].iloc[::-1]

    def __str__(self):
        return str(self._result)


def SMA(df, n):
    df['sma'] = df['close'].rolling(n).mean()
    return df['sma']

class TestStrategy(Strategy):
    sma = Indicator(SMA, params=(2,), prev=2)

    def next(self):
        print('here')


if __name__ == '__main__':
    data = {
        'open': [1,2,3,4,3,2,1,2,3,4,3,2,1],
        'high': [2,3,4,5,4,3,2,3,4,5,4,3,2],
        'low': [1,2,3,4,3,2,1,2,3,4,3,2,1],
        'close': [1.5,2.5,3.5,4.5,3.5,2.5,1.5,2.5,3.5,4.5,3.5,2.5,1.5]
    }
    x = BackTest(TestStrategy, data)
    x.run()