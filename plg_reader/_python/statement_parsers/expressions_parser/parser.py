from ...ir_builder_dt import IRFString, IRNode
from .atoms import parse_atom, parse_fstring, parse_paren
from .base import ExpressionParser as BaseExpressionParser
from .postfix import parse_postfix_chain


class ExpressionParser(BaseExpressionParser):
    def parse_atom(self) -> IRNode:
        return parse_atom(self)

    def parse_paren(self) -> IRNode:
        return parse_paren(self)

    def parse_fstring(self) -> IRFString:
        return parse_fstring(self)

    def parse_postfix_chain(self, node: IRNode) -> IRNode:
        return parse_postfix_chain(self, node)
