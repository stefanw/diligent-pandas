"""
Implementation of the Nelson rules
https://en.wikipedia.org/wiki/Nelson_rules

"""
from collections import deque

import numpy as np

from ..diligent import registry
from ..utils import is_numeric

__all__ = ['nelson_rule_%d' % i for i in range(1, 9)]


@registry.register(name='Nelson Rule 1', tags='nelson')
def nelson_rule_1(series, std_mult=3, mean=None, std=None):
    if not is_numeric(series):
        return

    message_inc = 'At {}: {} is three standard deviations above the mean of {}'
    message_dec = 'At {}: {} is three standard deviations below the mean of {}'

    if mean is None:
        mean = series.mean()
    if std is None:
        std = series.std()
    three_std = std_mult * std

    for i, x in series[series >= mean + three_std].iteritems():
        yield message_inc.format(i, x, mean)
    for i, x in series[series <= mean - three_std].iteritems():
        yield message_dec.format(i, x, mean)


@registry.register(name='Nelson Rule 2', tags='nelson')
def nelson_rule_2(series, threshold=9, mean=None):
    if not is_numeric(series):
        return

    message_below = 'At {}: {} data points in sequence are below the mean of {}'
    message_above = 'At {}: {} data points in sequence are above the mean of {}'

    if mean is None:
        mean = series.mean()
    above_counter = 0
    first_trend = None
    below_counter = 0
    for i, x in series.iteritems():
        if x > mean:
            if below_counter >= threshold:
                yield message_below.format(
                    first_trend, below_counter, mean)
            below_counter = 0
            if above_counter == 0:
                first_trend = i
            above_counter += 1

        elif x < mean:
            if above_counter >= threshold:
                yield message_above.format(
                    first_trend, above_counter, mean)
            above_counter = 0
            if below_counter == 0:
                first_trend = i
            below_counter += 1
        else:
            below_counter = 0
            above_counter = 0

    if above_counter >= threshold:
        yield message_above.format(
            first_trend, above_counter, mean)
    if below_counter >= threshold:
        yield message_below.format(
            first_trend, below_counter, mean)


@registry.register(name='Nelson Rule 3', tags='nelson')
def nelson_rule_3(series, threshold=6):
    if not is_numeric(series):
        return

    message_inc = 'At {}: {} data points in sequence are increasing'
    message_dec = 'At {}: {} data points in sequence are decreasing'

    trend_counter = 0
    last_value = None
    last_index = None
    first_row = None
    current_trend = None

    for i, x in series.iteritems():
        if last_value is None:
            last_value = x
            last_index = i
            continue
        trend = np.sign(x - last_value)
        if trend != current_trend:
            if trend_counter >= threshold:
                if current_trend > 0:
                    yield message_inc.format(
                        first_row, trend_counter)
                elif current_trend < 0:
                    yield message_dec.format(
                        first_row, trend_counter)
            first_row = last_index
            trend_counter = 1  # the first point was in last iteration
            current_trend = np.sign(x - last_value)

        last_value = x
        last_index = i
        if trend == 0:
            continue
        trend_counter += 1

    if trend_counter >= threshold:
        if current_trend > 0:
            yield message_inc.format(
                first_row, trend_counter)
        elif current_trend < 0:
            yield message_dec.format(
                first_row, trend_counter)


@registry.register(name='Nelson Rule 4', tags='nelson')
def nelson_rule_4(series, threshold=14):
    if not is_numeric(series):
        return

    message = 'At {}: {} data points in sequence alternate in direction'

    current_trend = 0
    trend_counter = 0
    values = deque([], 3)
    indizes = deque([], 3)
    first_index = None

    for i, x in series.iteritems():
        values.append(x)
        indizes.append(i)
        if len(values) < 2:
            continue
        trend = np.sign(x - values[-2])

        # Increasing (1) + decreasing (-1) == 0
        alternation = current_trend + trend == 0
        if first_index is None and alternation:
            first_index = indizes[0]
            trend_counter = 3  # Trend started two rows before
        elif first_index is not None and alternation:
            trend_counter += 1
        elif first_index is not None and not alternation:
            if trend_counter >= threshold:
                yield message.format(
                    first_index, trend_counter)
            first_index = None

        current_trend = trend

    if first_index is not None and trend_counter >= threshold:
        yield message.format(
            first_index, trend_counter)


def nelson_rule_5_6(series, std_mult=2, window=3, threshold=2,
                    mean=None, std=None):
    if not is_numeric(series):
        return

    if mean is None:
        mean = series.mean()
    if std is None:
        std = series.std()
    x_std = std_mult * std

    indizes = deque([], window)
    values = deque([], window)
    for i, x in series.iteritems():
        indizes.append(i)
        values.append(x)

        if len(indizes) < window:
            continue

        count_above = len([v for v in values if v > mean + x_std])
        if count_above >= threshold:
            yield 'At {}: {} out of {} points in a row are more than {} standard deviations above the mean.'.format(
                indizes[0], count_above, window, std_mult)

        count_below = len([v for v in values if v < mean - x_std])
        if count_below >= threshold:
            yield 'At {}: {} out of {} points in a row are more than {} standard deviations below the mean.'.format(
                indizes[0], count_below, window, std_mult)


@registry.register(name='Nelson Rule 5', tags='nelson')
def nelson_rule_5(series, mean=None, std=None):
    return nelson_rule_5_6(series, std_mult=2, window=3, threshold=2,
                           mean=mean, std=std)


@registry.register(name='Nelson Rule 6', tags='nelson')
def nelson_rule_6(series, mean=None, std=None):
    return nelson_rule_5_6(series, std_mult=1, window=5, threshold=4,
                           mean=mean, std=std)


def nelson_rule_7_8(series, std_mult=1, window=15, threshold=15, cmp=None,
                    message=None, mean=None, std=None):
    if not is_numeric(series):
        return

    if mean is None:
        mean = series.mean()
    if std is None:
        std = series.std()
    x_std = std_mult * std
    below = mean - x_std
    above = mean + x_std

    indizes = deque([], window)
    values = deque([], window)

    first_index = None
    count = 0

    for i, x in series.iteritems():
        indizes.append(i)
        values.append(x)

        if len(indizes) < window:
            continue

        count_within = len([v for v in values if cmp(below, v, above)])

        if first_index is None and count_within >= threshold:
            first_index = indizes[0]
            count = count_within
        elif first_index is not None and count_within >= threshold:
            count += 1
        elif first_index is not None:
            yield message.format(
                first_index, count)
            first_index = None
            count = 0

    if count > 0:
        yield message.format(
                    first_index, count)


@registry.register(name='Nelson Rule 7', tags='nelson')
def nelson_rule_7(series, mean=None, std=None):
    return nelson_rule_7_8(series, std_mult=1, window=15, threshold=15,
        cmp=lambda b, v, a: b <= v <= a,
        message='At {}: {} points in a row are all within 1 standard '
                'deviation of the mean on either side of the mean.',
        mean=mean, std=std)


@registry.register(name='Nelson Rule 8', tags='nelson')
def nelson_rule_8(series, mean=None, std=None):
    return nelson_rule_7_8(series, std_mult=1, window=8, threshold=8,
        cmp=lambda b, v, a: v < b or v > a,
        message='At {}: {} points in a row exist with none within 1 '
                'standard deviation of the mean and the points are in both '
                'directions from the mean.',
        mean=mean, std=std)
