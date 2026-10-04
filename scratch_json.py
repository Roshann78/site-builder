import json

titles = [
    'Normal',
    'With & and : and #',
    'With "quotes"',
    'With \\slash'
]

for t in titles:
    print(f"{t!r} -> {json.dumps(t)}")
