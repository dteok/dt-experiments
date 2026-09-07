"""Tests for pokefib.pokemon, with requests mocked (no live network calls)."""

from unittest.mock import Mock, patch

import pytest
import requests

from pokefib.pokemon import get_pokemon_abilities

MOCK_CHARMANDER_RESPONSE = {
    "abilities": [
        {"ability": {"name": "blaze"}, "is_hidden": False, "slot": 1},
        {"ability": {"name": "solar-power"}, "is_hidden": True, "slot": 3},
    ]
}


@patch("pokefib.pokemon.requests.get")
def test_get_pokemon_abilities_returns_ability_names(mock_get):
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = MOCK_CHARMANDER_RESPONSE
    mock_get.return_value = mock_response

    assert get_pokemon_abilities(5) == ["blaze", "solar-power"]
    mock_get.assert_called_once_with("https://pokeapi.co/api/v2/pokemon/5", timeout=10)


@patch("pokefib.pokemon.requests.get")
def test_get_pokemon_abilities_raises_on_http_error(mock_get):
    mock_response = Mock(status_code=404)
    mock_response.raise_for_status.side_effect = requests.HTTPError("Not Found")
    mock_get.return_value = mock_response

    with pytest.raises(requests.HTTPError):
        get_pokemon_abilities(99999)
