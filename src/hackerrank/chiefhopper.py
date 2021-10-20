#!/bin/python3

import math
import os
import random
import re
import sys

#
# Complete the 'chiefHopper' function below.
#
# The function is expected to return an INTEGER.
# The function accepts INTEGER_ARRAY arr as parameter.
#

## Reference: https://livecodestream.dev/video/password-cracker/
"""
initial_energy to be MIN
bot_energy >= 0

final_energy = 0  // min_energy

1. bot_energy < height:
    new_energy = bot_energy - (height - bot_energy)

2. bot_energy > height:
    new_energy = bot_energy + (bot_energy - height)
    >> ne = be + be - h
        ne = 2 * be - h  //this is exactly the same as 1 above.

3. bot_energy == height
    new_energy = bot_energy

We can simplify the equations in 1 & 2
    ne = be - h + be
    ne = 2 * be - h
    therefore, 
        be = (ne + h) / 2
    
    Therefore, when both_energy != height:
        bot_energy = (new_energy + height) / 2

"""


def chiefHopper(arr):
    min_energy = 0

    for height in reversed(arr):
        min_energy = math.ceil((min_energy + height) / 2)

    return min_energy


if __name__ == "__main__":
    fptr = open(
        os.environ.get(
            os.environ["DESKTOP_SESSION"], "../dt-experiments/chiefhopper.userout"
        ),
        "w",
    )

    n = int(input("Input integers: ").strip())

    arr = list(map(int, input().rstrip().split()))

    result = chiefHopper(arr)

    fptr.write(str(result) + "\n")

    fptr.close()
