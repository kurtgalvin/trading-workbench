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
    bb = Indicator(bollinger_bands, params=(20,2))

    def next(self):
        if self.data.close < self.bb.now.bb_lower:
            if not self.long_open:
                self.open_trade('long', n=1000)
        elif self.data.close > self.bb.now.bb_upper:
            if not self.short_open:
                self.open_trade('short', n=1000)

        if self.data.close > self.bb.now.bb_mid and self.long_open:
            self.close_trade('long')
        elif self.data.close < self.bb.now.bb_mid and self.short_open:
            self.close_trade('short')

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
    # plt.plot(x.df[['close', 'bb_upper', 'bb_mid', 'bb_lower']])
    # plt.show()
    x.run()