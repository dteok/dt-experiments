"""Client for fetching Pokemon data from PokeAPI (https://pokeapi.co)."""

import requests

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/pokemon"
REQUEST_TIMEOUT_SECONDS = 10


def get_pokemon_abilities(pokemon_id: int) -> list[str]:
    """Fetch a Pokemon's abilities from PokeAPI.

    :param pokemon_id: The Pokemon's numeric ID.
    :return: List of ability names, e.g. ["blaze", "solar-power"].
    :raises requests.HTTPError: If the API request fails.
    """
    url = f"{POKEAPI_BASE_URL}/{pokemon_id}"
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    data = response.json()
    return [entry["ability"]["name"] for entry in data["abilities"]]


if __name__ == "__main__":
    print(get_pokemon_abilities(51))