from pathlib import Path

from plg_reader._python.parse_file import FileParser

text = FileParser.parse(Path(__file__), False)

"""
t
e
s
t
"""

for t in text:
    print(t.tokens)
