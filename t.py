from pathlib import Path

from plg_reader._python_reader.raw_line_builder import RawLineBuilder

for line in RawLineBuilder.read_file_to_tokens(Path(__file__)):
    print(line.raw_strs)
