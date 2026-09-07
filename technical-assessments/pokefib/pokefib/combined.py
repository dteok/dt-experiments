"""Combine Fibonacci numbers with Pokemon ability lookups."""

from pokefib.fibonacci import fibonacci
from pokefib.pokemon import get_pokemon_abilities
import argparse


def get_abilities_and_fibonacci(n: int) -> dict[str, list[str] | int]:
    """Return a Pokemon's abilities and the Fibonacci number for the same n.

    :param n: Used both as the Pokemon ID and the Fibonacci sequence position.
    :return: Dict with "abilities" (list[str]) and "fibonacci" (int).
    """
    return {
        "abilities": get_pokemon_abilities(n),
        "fibonacci": fibonacci(n),
    }


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Get Pokemon abilities.',
        usage='%(prog)s input_number'
        )
    parser.add_argument('num', type=int, help='Enter your Pokemon ID.')
    args = parser.parse_args()

    print(get_pokemon_abilities(args.num))
