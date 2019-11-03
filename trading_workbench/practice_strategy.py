import matplotlib.pyplot as plt
from core import BackTest, Strategy, Indicator
import sys

sys.path.insert(1, 'C:/Users/Kurt/Desktop/Maverick/maverick')
from fabricator import Fabricator


def SMA(df, n):
    df['sma'] = df['close'].rolling(n).mean()
    return df['sma']

def bollinger_bands(df, n, dev):
    deviation = df['close'].rolling(n).std()*dev
    df['bb_mid'] = df['close'].rolling(n).mean()
    df['bb_upper'] = df['bb_mid'] + deviation
    df['bb_lower'] = df['bb_mid'] - deviation
    return df[['bb_upper', 'bb_mid', 'bb_lower']]

class TestStrategy(Strategy):
    class Meta:
        plot=['close', 'bb_upper', 'bb_mid', 'bb_lower']
        # spread = 1.4/10_000
        price = 'M'

    bb = Indicator(bollinger_bands, params=(20,2))

    def next(self):
        pos_long = self.positions_long
        pos_short = self.positions_short
        
        # open
        if self.data.open < self.bb.now.bb_lower and self.data.close > self.bb.now.bb_lower:
            stop_price = self.bb.now.bb_lower - (self.bb.now.bb_mid - self.bb.now.bb_lower)
            self.open_position('long', n=10000, stop_price=stop_price)
        elif self.data.open > self.bb.now.bb_upper and self.data.close < self.bb.now.bb_upper:
            stop_price = self.bb.now.bb_upper + (self.bb.now.bb_upper - self.bb.now.bb_mid)
            self.open_position('short', n=10000, stop_price=stop_price)

        #close
        if self.data.close > self.bb.now.bb_mid and pos_long:
            self.close_positions('long')
        elif self.data.close < self.bb.now.bb_mid and pos_short:
            self.close_positions('short')

if __name__ == '__main__':
    data = Fabricator({'file': 'env/oanda.ini'}, 'EUR_USD', 'M5')
    candles = data.candles(100_000)
    data = {
        'open': candles[0],
        'high': candles[1],
        'low': candles[2],
        'close': candles[3]
    }
    x = BackTest(TestStrategy, data)
    x.results()
    x.plot()