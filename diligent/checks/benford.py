"""
Implementation of the Benford's law
https://en.wikipedia.org/wiki/Nelson_rules

"""
import math

from ..diligent import registry
from ..utils import is_numeric

__all__ = ['benfords_law']


def get_most_signifcant_digit(x):
    x = abs(x)
    e = math.floor(math.log10(x))
    return int(x * (10 ** -e))


@registry.register(name="Benford's law", tags='benford')
def benfords_law(series):
    if not is_numeric(series):
        return

    actual = series[series != 0].dropna().apply(get_most_signifcant_digit).value_counts()

    total = actual.sum()
    # expected number of each leading digit per Benford's law
    expected = [total * math.log10(1 + 1.0 / i) for i in range(1, 10)]

    for i, x in actual.iteritems():
        yield 'Digit {} appeared {}, expected {}'.format(i, x, round(expected[(i - 1)]))
