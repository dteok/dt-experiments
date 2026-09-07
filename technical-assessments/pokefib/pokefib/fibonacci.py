"""Iterative Fibonacci sequence calculator."""


def fibonacci(n: int) -> int:
    """Return the n-th Fibonacci number (0-indexed: fib(0)=0, fib(1)=1).

    :param n: Position in the Fibonacci sequence (non-negative integer).
    :return: The Fibonacci number at position n.
    :raises ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("n must be a non-negative integer")

    previous, current = 0, 1
    for _ in range(n):
        previous, current = current, previous + current
    return previous

def fibonacci_sequence(n: int) -> list[int]:
    """Return a list of Fibonacci numbers given n.

    :param n: Position in the Fibonacci sequence
    :return: The list of Fibonacci numbers up to postion n.
    :raises ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be a positive integer")

    if n == 0:
        return [0]
    if n == 1:
        return [1]

    sequence = [0, 1]

    for _ in range(1, n):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence


# if __name__ == "__main__":
#     position = 12
#     print(fibonacci(position))
#     print(fibonacci_sequence(position))