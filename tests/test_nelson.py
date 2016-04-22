import pandas as pd

from diligent.checks.nelson import (nelson_rule_1, nelson_rule_2, nelson_rule_3, nelson_rule_4,
                     nelson_rule_5, nelson_rule_6, nelson_rule_7, nelson_rule_8)


def test_nelson_rule_1():
    mean = 0.0
    std = 1.0
    s = pd.Series([3, -3, 2, -2])
    messages = list(nelson_rule_1(s, mean=mean, std=std))
    assert len(messages) == 2
    assert messages[0] == 'At 0: 3 is three standard deviations above the mean of %s' % s.mean()
    assert messages[1] == 'At 1: -3 is three standard deviations below the mean of %s' % s.mean()


def test_nelson_rule_2():
    mean = 0.0
    messages = list(nelson_rule_2(pd.Series(range(1, 10)), mean=mean))
    assert len(messages) == 1
    assert messages[0] == 'At 0: 9 data points in sequence are above the mean of %s' % mean

    messages = list(nelson_rule_2(pd.Series(range(-1, -10, -1)), mean=mean))
    assert len(messages) == 1
    assert messages[0] == 'At 0: 9 data points in sequence are below the mean of %s' % mean

    messages = list(nelson_rule_2(pd.Series(range(-4, 5)), mean=mean))
    assert len(messages) == 0


def test_nelson_rule_3():
    messages = list(nelson_rule_3(pd.Series(range(6))))
    assert len(messages) == 1
    assert messages[0] == 'At 0: 6 data points in sequence are increasing'

    messages = list(nelson_rule_3(pd.Series(range(0, -6, -1))))
    assert len(messages) == 1
    assert messages[0] == 'At 0: 6 data points in sequence are decreasing'

    messages = list(nelson_rule_3(pd.Series([0, 1, 0, 1, 0, 1])))
    assert len(messages) == 0

    messages = list(nelson_rule_3(pd.Series([0, 0, 0, 0, 0, 0])))
    assert len(messages) == 0


def test_nelson_rule_4():
    messages = list(nelson_rule_4(pd.Series([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1])))
    assert len(messages) == 1
    assert messages[0] == 'At 0: 14 data points in sequence alternate in direction'

    messages = list(nelson_rule_4(pd.Series([0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1])))
    assert len(messages) == 0


def test_nelson_rule_5():
    mean = 0.0
    std = 1.0
    messages = list(nelson_rule_5(pd.Series([2.1, 1, 2.1]), mean=mean, std=std))
    assert len(messages) == 1
    assert messages[0] == ('At 0: 2 out of 3 points in a row are more than '
                           '2 standard deviations above the mean.')

    messages = list(nelson_rule_5(pd.Series([-2.1, 1, -2.1]), mean=mean, std=std))
    assert len(messages) == 1
    assert messages[0] == ('At 0: 2 out of 3 points in a row are more than '
                          '2 standard deviations below the mean.')

    messages = list(nelson_rule_5(pd.Series([2.1, 1, -2.1]), mean=mean, std=std))
    assert len(messages) == 0

    messages = list(nelson_rule_5(pd.Series([2.0, 1, 2.1]), mean=mean, std=std))
    assert len(messages) == 0


def test_nelson_rule_6():
    mean = 0.0
    std = 1.0
    messages = list(nelson_rule_6(pd.Series([2, 1.1, 2, 0, 1.5]), mean=mean, std=std))
    assert len(messages) == 1
    assert messages[0] == 'At 0: 4 out of 5 points in a row are more than 1 standard deviations above the mean.'

    messages = list(nelson_rule_6(pd.Series([-2, -1.1, -2, 0, -1.5]), mean=mean, std=std))
    assert len(messages) == 1
    assert messages[0] == 'At 0: 4 out of 5 points in a row are more than 1 standard deviations below the mean.'

    messages = list(nelson_rule_6(pd.Series([2, 1.1, -2, 0, 1.5]), mean=mean, std=std))
    assert len(messages) == 0

    messages = list(nelson_rule_6(pd.Series([0.5, 1, 0.5, 4, 0]), mean=mean, std=std))
    assert len(messages) == 0


def test_nelson_rule_7():
    mean = 0.0
    std = 1.0
    messages = list(nelson_rule_7(pd.Series([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]),
                                  mean=mean, std=std))
    assert len(messages) == 1
    assert messages[0] == ('At 0: 15 points in a row are all within 1 standard '
                          'deviation of the mean on either side of the mean.')

    messages = list(nelson_rule_7(pd.Series([0, 1, 0, 1, 1, 2, 1, 1, 0, 1, 0, 1, 0, 1, 0]),
                                  mean=mean, std=std))
    assert len(messages) == 0


def test_nelson_rule_8():
    mean = 0.0
    std = 1.0
    messages = list(nelson_rule_8(pd.Series([2, 4, 2, -4, 6, -10, 7, 2]),
                                  mean=mean, std=std))
    assert len(messages) == 1
    assert messages[0] == ('At 0: 8 points in a row exist with none within 1 '
                           'standard deviation of the mean and the points are in both '
                           'directions from the mean.')

    messages = list(nelson_rule_8(pd.Series([2, 0, 2, -4, 6, 0, 7, 2]),
                                  mean=mean, std=std))
    assert len(messages) == 0
