from pathlib import Path

from plg_reader._python_reader.text_to_tokens import PyRead

p = PyRead.read_file_to_tokens(
    Path(r"F:\Desktop\plg\plg-reader\plg_reader\_python_reader\text_to_tokens.py")
)

for line in p:
    print(line.raw_strs)
