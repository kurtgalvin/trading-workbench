import pandas as pd
import numpy as np
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

def apply_spread(price: float, spread: float, transaction: str, price_type: str) -> float:
    ''' Get the price with spread applied 
    Args
    ----
    price: Probably closing price of candle. \n
    spread: Spread of the instrument. \n
    transaction: buy or sell, 
        buy if opening long or closing short,
        sell if opening short or closing long. \n
    price_type: B for bid, M for mid, A for ask. 
        describes the type of price and if spread should be applied \n
    '''
    spread = spread/2 if price_type.upper() == 'M' and spread > 0 else spread
    if transaction == 'buy' and price_type.upper() != 'A':
        price += spread
    elif transaction == 'sell' and price_type.upper() != 'B':
        price -= spread
    return price


class Meta:
    pass


class BackTest:
    def __init__(self, strategy, data):
        print("Running Backtest.")
        self.strategy = strategy(data)

    @property
    def df(self):
        return self.strategy.df

    @property
    def positions(self):
        return self.strategy.closed_positions

    def results(self):
        total_profit = 0
        wins = []
        losses = []
        for i in self.positions:
            if i.profit > 0:
                wins.append(i.profit)
            if i.profit <= 0:
                losses.append(i.profit)
            total_profit += i.profit
        print("Profit:", round(total_profit, 3))
        print("Wins:", len(wins), "Avg:", round(sum(wins)/len(wins), 3), "Top:", top_of_list(wins, 5, 'max'), "Top 100 avg:", round(sum(top_of_list(wins, 100, 'max'))/100, 3))
        print("Losses:", len(losses), "Avg:", round(sum(losses)/len(losses), 3), "Top:", top_of_list(losses, 5, 'min'), "Top 100 avg:", round(sum(top_of_list(losses, 100, 'min'))/100, 3))
    
    def plot(self):
        if hasattr(self.strategy, '_meta'):
            for i in self.strategy._meta['plot']:
                plt.plot(self.df[i])
        else:
            plt.plot(self.df.close)
        long_pos = list(filter(lambda x: x.is_long, self.positions))
        short_pos = list(filter(lambda x: x.is_short, self.positions))
        plt.plot([i.index for i in long_pos], [i.price for i in long_pos], '>', color='#77dd77')
        plt.plot([i.close_index for i in long_pos], [i.close_price for i in long_pos], '<', color='#77dd77')
        plt.plot([i.index for i in long_pos], [i.stop_price for i in long_pos], 'd', color='#77dd77')

        plt.plot([i.index for i in short_pos], [i.price for i in short_pos], '>', color='#ff6961')
        plt.plot([i.close_index for i in short_pos], [i.close_price for i in short_pos], '<', color='#ff6961')
        plt.plot([i.index for i in short_pos], [i.stop_price for i in short_pos], 'd', color='#ff6961')

        plt.show()


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
        self.index = largest_prev + largest_valid + self._meta['historical_count']
        self.max_index = df.last_valid_index()
        self.__loop()

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
        assert direction in ['long', 'short'], f"direction must be long or short, not {direction}"
        transaction = 'buy' if direction == 'long' else 'sell' 
        price = apply_spread(self.data.close, self._meta['spread'], transaction, self._meta['price'])
        historical_data = self.df.iloc[self.index-self._meta['historical_count']:self.index].reset_index(drop=True)
        historical_data = historical_data if len(historical_data) else None
        self._positions.append(Position(
            price, 
            direction, 
            n, 
            self.index, 
            stop_price=stop_price, 
            history=historical_data,
            time=self.data.datetime
        ))

    def close_position(self, position=None):
        ''' Close one position
        '''
        if not position:
            pos = self._positions.pop(0)
        elif position in self._positions:
            closed_pos_index = self._positions.index(position)
            pos = self._positions.pop(closed_pos_index)
        else:
            pos = position
        transaction = 'buy' if pos.direction == 'short' else 'sell'
        price = apply_spread(self.data.close, self._meta['spread'], transaction, self._meta['price'])
        self.closed_positions.append(pos.close(price, self.index))

    def close_positions(self, direction='all'):
        ''' Close all positions in a given direction.
        '''
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
            self.close_position(position=pos)

    def trigger_stops(self):
        for pos in self._positions.copy():
            if pos.is_stop_triggered(self.data.close):
                pos_index = self._positions.index(pos)
                pos_obj = self._positions.pop(pos_index).close(self.data.close, self.index)
                self.closed_positions.append(pos_obj)

    def __loop(self):
        self._positions = []
        self.closed_positions = []
        while self.index <= self.max_index:
            self.trigger_stops()
            self.next()
            self.index += 1

    @staticmethod
    def __validate_meta(meta: Meta) -> dict:
        meta_fields = {
            'plot': lambda x: isinstance(x, list),
            'historical_count': lambda x: isinstance(x, int),
            'spread': lambda x: isinstance(x, (float, int)),
            'price': lambda x: isinstance(x, str) and x.upper() in ['B', 'M', 'A']
        }
        results = {
            'plot': ['close'],
            'historical_count': 0,
            'spread': 0,
            'price': 'M'
        }
        for k, v in meta.__dict__.items():
            if k in meta_fields: 
                if meta_fields[k](v):
                    results[k] = v
                else:
                    raise ValueError(f'unsupported value or type: {v} for {k} in Strategy.Meta')
        return results


    def __init_subclass__(cls):
        if hasattr(cls, 'Meta'):
            cls._meta = cls.__validate_meta(cls.Meta)
            delattr(cls, 'Meta')
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
    def __init__(self, price, direction, n, index, stop_price=False, history=None, time=None):
        self.price = price
        self.direction = direction
        self.n = n
        self.index = index
        self.stop_price = stop_price
        self.history = history
        self.time = time
        self.profit = 0

    @property
    def is_long(self):
        return bool(self.direction == 'long')

    @property
    def is_short(self):
        return bool(self.direction == 'short')

    @property
    def is_profitable(self):
        return bool(self.profit > 0)

    def move_stop(self, stop_price):
        self.stop_price = stop_price

    def is_stop_triggered(self, price):
        ''' a check to see if the current price will trigger the stop
        '''
        if not self.stop_price:
            return False

        if self.direction == 'long' and price <= self.stop_price:
            return True
        elif self.direction == 'short' and price >= self.stop_price:
            return True
        return False
    
    def close(self, price, index):
        self.close_price = price
        self.close_index = index
        if self.direction == 'long':
            self.profit += (price-self.price)*self.n
        elif self.direction == 'short':
            self.profit += (self.price-price)*self.n
        return self


if __name__ == '__main__':
    print(top_of_list([1, 2, 2, 1, 4, 6, 2, 3], 4, 'min'))