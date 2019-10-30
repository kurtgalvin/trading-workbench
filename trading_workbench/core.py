import pandas as pd
import matplotlib.pyplot as plt


def top_of_list(list_: list, n: int, mm: str) -> list:
    ''' Get a list of the top values by min or max.
    Args
    ----
    list_ : all the values.\n
    n : number of top results to display.\n
    mm : 'min' or 'max' top results. \n
    '''
    is_max = bool(mm.lower() == 'max')
    is_min = bool(mm.lower() == 'min')
    result = []
    for li in list_:
        if len(result) < n:
            for i, res in enumerate(result):
                if is_max and li >= res:
                    result.insert(i, li)
                    break
                elif is_min and li <= res:
                    result.insert(i, li)
                    break
            else:
                result.append(li)
        else:
            for i, res in enumerate(result):
                if is_max and li >= res:
                    result = result[:i] + [li] + result[i:len(result)-1]
                    break
                if is_min and li <= res:
                    result = result[:i] + [li] + result[i:len(result)-1]
                    break
    return [round(i, 3) for i in result]


class BackTest:
    def __init__(self, strategy, data):
        self.strategy = strategy(data)

    @property
    def df(self):
        return self.strategy.df

    def run(self):
        for i in self.strategy:
            pass
        total_profit = 0
        wins = []
        losses = []
        for i in self.strategy.closed_positions:
            if i.profit > 0:
                wins.append(i.profit)
            if i.profit < 0:
                losses.append(i.profit)
            total_profit += i.profit
        print("Profit:", total_profit)
        print("Wins:", len(wins), "Avg:", sum(wins)/len(wins), "Top:", top_of_list(wins, 5, 'max'), "Top 100 avg:", sum(top_of_list(wins, 100, 'max'))/100)
        print("Losses:", len(losses), "Avg:", sum(losses)/len(losses), "Top:", top_of_list(losses, 5, 'min'), "Top 100 avg:", sum(top_of_list(losses, 100, 'min'))/100)


class Strategy:
    def __init__(self, data):
        self._positions = []
        self.closed_positions = []
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
    def positions(self):
        return self._positions

    @property
    def positions_long(self):
        return list(filter(lambda x: x.is_long, self._positions))

    @property
    def positions_short(self):
        return list(filter(lambda x: x.is_short, self._positions))

    def open_position(self, direction, n=1, stop_price=False):
        self._positions.append(Position(self.data.close, direction, n, self.index, stop_price=stop_price))

    def close_position(self, position=None):
        if not position:
            self.closed_positions.append(self._positions.pop(0).close(self.data.close))
        else:
            closed_pos_index = self._positions.index(position)
            closed_pos = self._positions.pop(closed_pos_index).close(self.data.close)
            self.closed_positions.append(closed_pos)

    def close_positions(self, direction='all'):
        positions_to_close = None
        if direction.lower() == 'long':
            positions_to_close = self.positions_long
            self._positions = self.positions_short
        elif direction.lower() == 'short':
            positions_to_close = self.positions_short
            self._positions = self.positions_long
        else:
            positions_to_close = self._positions
            self._positions = []
        for pos in positions_to_close:
            self.closed_positions.append(pos.close(self.data.close))
        return 

    def trigger_stops(self):
        for pos in self._positions:
            pos.trigger_stop(self.data.close)

    def __iter__(self):
        self._positions = []
        self.closed_positions = []
        return self

    def __next__(self):
        if self.index <= self.max_index:
            self.trigger_stops()
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
    def __init__(self, price, direction, n, index, stop_price=False):
        self.price = price
        self.direction = direction
        self.n = n
        self.index = index
        self.stop_price = stop_price
        self.profit = 0

    @property
    def is_long(self):
        return bool(self.direction == 'long')

    @property
    def is_short(self):
        return bool(self.direction == 'short')

    def move_stop(self, stop_price):
        self.stop_price = stop_price

    def trigger_stop(self, price):
        if not self.stop_price:
            return False

        if self.direction == 'long' and price < self.stop_price:
            self.close(price)
            return True
        elif self.direction == 'short' and price > self.stop_price:
            self.close(price)
            return True
        return False
    
    def close(self, price):
        self.close_price = price
        if self.direction == 'long':
            self.profit += (price-self.price)*self.n
        elif self.direction == 'short':
            self.profit += (self.price-price)*self.n
        return self

if __name__ == '__main__':
    print(top_of_list([1, 2, 2, 1, 4, 6, 2, 3], 4, 'min'))