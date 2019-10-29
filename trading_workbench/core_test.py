import pytest
import pandas as pd

from core import Strategy, Indicator

@pytest.fixture
def build_strategy():
    class SMA(Indicator):
        def __init__(self, n):
            self.n = n
    
        def __get__(self, strategy, owner):
            close = strategy.df['close']
            return close.rolling(self.n).mean()

    class TestStrategy(Strategy):
        sma = SMA(2)
    
    data = {
        'open': [1,2,3,4,3,2,1,2,3,4,3,2,1],
        'high': [2,3,4,5,4,3,2,3,4,5,4,3,2],
        'low': [1,2,3,4,3,2,1,2,3,4,3,2,1],
        'close': [1.5,2.5,3.5,4.5,3.5,2.5,1.5,2.5,3.5,4.5,3.5,2.5,1.5]
    }
    return TestStrategy(data)

def test_df(build_strategy):
    assert isinstance(build_strategy.df, pd.DataFrame), "`df` is not `DataFrame`"

def test_strategy_indicators(build_strategy):
    assert hasattr(build_strategy, '_indicators'), "No `_indicators`"
    assert isinstance(build_strategy._indicators, dict), "`_indicators` is not dict"
    assert build_strategy._indicators.get('sma', False), "`_indicators` has no `sma`"

def test_dataframe(build_strategy):
    df = pd.DataFrame({
        'open': [1,2,3,4,3,2,1,2,3,4,3,2,1],
        'high': [2,3,4,5,4,3,2,3,4,5,4,3,2],
        'low': [1,2,3,4,3,2,1,2,3,4,3,2,1],
        'close': [1.5,2.5,3.5,4.5,3.5,2.5,1.5,2.5,3.5,4.5,3.5,2.5,1.5],
        'sma': [None, 2.0, 3.0, 4.0, 4.0, 3.0, 2.0, 2.0, 3.0, 4.0, 4.0, 3.0, 2.0]
    })
    assert df.equals(build_strategy.df), "dataframe does not match"