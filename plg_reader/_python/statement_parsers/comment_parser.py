from __future__ import annotations

from ..file_parse_dt import Line, TokenType
from ..ir_builder_dt import IRComment, IRNode


class CommentParser:
    @staticmethod
    def parse(line: Line) -> IRNode | None:
        tokens = line.tokens
        if not tokens or not all(t.type == TokenType.COMMENT for t in tokens):
            return None

        text = " ".join(t.data for t in tokens)
        return IRComment(pos=tokens[0].pos, text=text)
