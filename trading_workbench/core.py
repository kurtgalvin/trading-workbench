import pandas as pd


class BackTest:
    def __init__(self, strategy, data):
        self.strategy = strategy(data)

    def run(self):
        for i in self.strategy:
            pass
        total_profit = 0
        for i in self.strategy.positions:
            total_profit += i.profit
        print(total_profit)


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

        self.df = df
        self.index = largest_prev + largest_valid
        self.max_index = df.last_valid_index()

    @property
    def data(self):
        return self.df.iloc[self.index]

    @property
    def long_open(self):
        return bool(self.long_pos)

    @property
    def short_open(self):
        return bool(self.short_pos)

    def open_trade(self, direction, n=1):
        if direction == 'long':
            if self.long_pos:
                self.long_pos.add_n(self.data.close, n, self.index)
            else:
                self.long_pos = Position(self.data.close, direction, n, self.index)
        elif direction == 'short':
            if self.short_pos:
                self.short_pos.add_n(self.data.close, n, self.index)
            else:
                self.short_pos = Position(self.data.close, direction, n, self.index)

    def close_trade(self, direction):
        if direction == 'long' and self.long_pos:
            self.positions.append(self.long_pos.close(self.data.close))
            self.long_pos = None
        elif direction == 'short' and self.short_pos:
            self.positions.append(self.short_pos.close(self.data.close))
            self.short_pos = None

    def __iter__(self):
        self.positions = []
        self.long_pos = None
        self.short_pos = None
        return self

    def __next__(self):
        if self.index <= self.max_index:
            self.next()
            self.index += 1
            return self.index - 1
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


class Position:
    def __init__(self, price, direction, n, index):
        self.transactions = [{
            'price': price,
            'n': n,
            'index': index
        }]
        self.profit = 0
        self.open = True
        self.direction = direction

    def add_n(self, price, n, index):
        self.transactions.append({
            'price': price,
            'n': n,
            'index': index
        })
    
    def close(self, price):
        self.open = False
        self.close_price = price
        for t in self.transactions:
            if self.direction == 'long':
                self.profit += (price-t['price'])*t['n']
            elif self.direction == 'short':
                self.profit += (t['price']-price)*t['n']
        return self




def SMA(df, n):
    df['sma'] = df['close'].rolling(n).mean()
    return df['sma']

class TestStrategy(Strategy):
    sma = Indicator(SMA, params=(2,), prev=2)

    def next(self):
        if self.data.close > self.sma.now:
            if self.short_open:
                self.close_trade('short')
            if not self.long_open:
                self.open_trade('long')
        else:
            if self.long_open:
                self.close_trade('long')
            if not self.short_open:
                self.open_trade('short')


if __name__ == '__main__':
    data = {
        'open': [1,2,3,4,3,2,1,2,3,4,3,2,1],
        'high': [2,3,4,5,4,3,2,3,4,5,4,3,2],
        'low': [1,2,3,4,3,2,1,2,3,4,3,2,1],
        'close': [1.5,2.5,3.5,4.5,3.5,2.5,1.5,2.5,3.5,4.5,3.5,2.5,1.5]
    }
    x = BackTest(TestStrategy, data)
    x.run()