from pathlib import Path

from plg_reader._python.logic_builder import LineBuilder
from plg_reader._python.raw_line_builder import RawLineBuilder

raw_line = RawLineBuilder.read_file_to_raw_lines(Path(__file__))
lines = LineBuilder.raw_lines_to_lines(raw_line)


for line in lines:
    print(line.tokens)
