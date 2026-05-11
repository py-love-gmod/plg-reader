from .file_parse_dt import Line
from .ir_builder_dt import IRNode


class IRBuilder:
    @classmethod
    def build(cls, tokens: list[Line]) -> list[IRNode]:
        pass
