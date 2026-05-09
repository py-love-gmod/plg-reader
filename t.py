from pathlib import Path

from plg_reader._python.parse_file import FileParser

text = FileParser.parse(Path(__file__), False)

"""
t
e
s
t
"""

t = r"ddd"
b"00"
rf"foo {t=}"

# Комментарий
for t in text:  # Комментарий
    print(t.tokens)
