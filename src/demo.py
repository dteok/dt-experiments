import re


data = {"a": 0, "b": [[1, 2], [3, 4]], "c": 5}


def hello(first: bool, second: bool):
    if first and second:
        raise ValueError("no")
    elif first:
        print("hello world")
    elif second:
        print("hello second")
    return "done!"


# import os
# print(os.getcwd())

phone_numbers = []
pattern = r"\(([\d\-+]+)\)"
"""
(  ([\d\-+]+)  )

(+49-30-833-931-313)
"""

with open("../dt-experiments/data/input/messylog.txt", "r") as f:
    for line in f:
        result = re.search(pattern, line)
        phone_numbers.append(result.group(1))

print(f"Extracted phone numbers: {phone_numbers}")

print("-+--" * 20)

# To better understand re's group() or capturing group, consider the following example
another_pattern = r"(.*) (.*) (.*)"
another_line = "Ada Lovelace fiesta stars from November"
another_result = re.search(another_pattern, another_line)

print(another_result)
print(f"This is groups(): {another_result.groups()}")
print(f"This is group(0): {another_result.group(0)}")
print(f"This is group(1): {another_result.group(1)}")
print(f"This is group(2): {another_result.group(2)}")
print(f"This is group(3): {another_result.group(3)}")

print("End of script")
