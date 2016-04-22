import re

import pandas as pd

from .. import registry, message
from ..utils import is_numeric


__all__ = ['show_data_type', 'count_nan', 'count_zeroes',
           'detect_suspicious_values', 'detect_repdigits', 'duplicate_rows',
           'suspicious_dataset_length',
           'duplicate_values']


@registry.register(name='Data Type', tags='basic')
def show_data_type(series):
    yield '{}'.format(series.dtype)


@registry.register(name='Count NaN', tags='basic')
def count_nan(series):
    nan_count = len(series[series.isnull()])
    yield '{} NaN values'.format(nan_count)


@registry.register(name='Count Zeroes', tags='basic')
def count_zeroes(series):
    zero_count = len(series[series == 0])
    yield '{} values are 0'.format(zero_count)


@registry.register(name='Detect suspicious values', tags='basic')
def detect_suspicious_values(series):
    suspicious = [65535, 2147483647, 4294967295]
    for number in suspicious:
        count = len(series[series == number])
        if count > 0:
            yield 'Suspicious number {} appears {} times'.format(number, count)


@registry.register(name='Detect repeated digits', tags='basic')
def detect_repdigits(series, digit_count=6):
    digits = range(1, 10)
    repdigits = [d * (10 ** n - 1) / 9 for d in digits for n in range(2, digit_count)]
    repdigits = repdigits + [x * -1 for x in repdigits]
    for repdigit in repdigits:
        count = (series == repdigit).sum()
        if count > 0:
            yield 'The value {} appears {} times'.format(repdigit, count)


@registry.register(name='Susipicous dataframe length', tags='basic', dataframe=True)
def suspicious_dataset_length(df, threshold=5):
    suspicious = [65535, 1048576]
    df_len = len(df)
    for number in suspicious:
        if df_len > number - threshold and df_len < number - threshold:
            yield 'Dataframe length is suspicious: {}'.format(df_len)


@registry.register(name='Duplicate rows', tags='basic', dataframe=True)
def duplicate_rows(df):
    duplicates = df[df.duplicated(keep=False)]
    first_duplicates = duplicates[~duplicates.duplicated()]
    for i, dup in first_duplicates.iterrows():
        if dup.isnull().all():
            # Don't deal with full NaN rows
            continue
        count = (duplicates == dup).sum().iloc[0] - 1
        yield message('{} duplicates for the following row'.format(count), rows=dup.to_frame().T.index)


@registry.register(name='Duplicate values', tags='basic')
def duplicate_values(series):
    duplicates = series[series.duplicated(keep=False)]
    first_duplicates = duplicates[~duplicates.duplicated()]
    for dup in first_duplicates:
        if pd.isnull(dup):
            # Don't deal with full values here
            continue
        count = (duplicates == dup).sum() - 1
        yield message('{} duplicates for the value {}'.format(
                count, dup), rows=[(duplicates == dup).index[0]])

BAD_NUM_RE = re.compile('^[\d\., ]+$')


@registry.register(name='Possibly numeric', tags='basic')
def possibly_numeric(series):
    if is_numeric(series):
        return
    non_na_series = series.dropna()
    total_values = len(non_na_series)
    count_numeric_values = non_na_series.str.match(BAD_NUM_RE).sum()
    yield '{} out of {} ({}%) of non-null values appear numeric'.format(
        count_numeric_values, total_values,
        round(count_numeric_values / float(total_values) * 100)
    )
