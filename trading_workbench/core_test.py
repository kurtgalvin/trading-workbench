import pytest
import pandas as pd

from core import Strategy

@pytest.fixture
def build_strategy():
    class TestStrategy(Strategy):
        pass
    
    data = {
        'open': [1,2,3,4,3,2,1],
        'high': [2,3,4,5,4,3,2],
        'low': [1,2,3,4,3,2,1],
        'close': [1.5,2.5,3.5,4.5,3.5,2.5,1.5]
    }
    return TestStrategy(data)

def test_df(build_strategy):
    assert isinstance(build_strategy.df, pd.DataFrame), "`df` is not `DataFrame`"