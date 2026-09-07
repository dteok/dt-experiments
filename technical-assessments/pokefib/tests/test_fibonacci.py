"""Tests for pokefib.fibonacci."""

import pytest

from pokefib.fibonacci import fibonacci
from pokefib.fibonacci import fibonacci_sequence


@pytest.mark.parametrize(
    "n, expected",
    [
        (0, 0),
        (1, 1),
        (2, 1),
        (3, 2),
        (4, 3),
        (5, 5),
        (10, 55),
        (12, 144)
    ],
)

def test_fibonacci_known_values(n, expected):
    assert fibonacci(n) == expected


@pytest.mark.parametrize(
        "n, exp_list",
        [
            (0, [0]),
            (1, [1]),
            (5, [0, 1, 1, 2, 3, 5]),
            (8, [0, 1, 1, 2, 3, 5, 8, 13, 21]),
            (12, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144])
        ]
)
def test_fibonacci_sequence_list(n, exp_list):
    assert fibonacci_sequence(n) == exp_list


def test_fibonacci_negative_raises_value_error():
    with pytest.raises(ValueError):
        fibonacci(-1)
