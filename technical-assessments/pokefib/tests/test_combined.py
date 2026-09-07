"""Tests for pokefib.combined."""

from unittest.mock import patch

from pokefib.combined import get_abilities_and_fibonacci


@patch("pokefib.combined.get_pokemon_abilities")
def test_get_abilities_and_fibonacci(mock_get_abilities):
    mock_get_abilities.return_value = ["blaze", "solar-power"]

    actual_result = get_abilities_and_fibonacci(5)

    assert actual_result == {"abilities": ["blaze", "solar-power"], "fibonacci": 5}
    mock_get_abilities.assert_called_once_with(5)
