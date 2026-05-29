import pytest

from plg_reader import (
    IRAttribute,
    IRBinOp,
    IRBinOpType,
    IRCall,
    IRConstant,
    IRIfExpr,
    IRName,
    IRSubscript,
    IRTuple,
    IRUnaryOp,
)


@pytest.mark.parametrize(
    "code, expected",
    [
        ("x = 42", 42),
        ("x = 3.14", 3.14),
        ("x = 'hello'", "'hello'"),
    ],
)
def test_constant(parse_code, code, expected):
    ir = parse_code(code)
    val = ir.body[0].value
    assert isinstance(val, IRConstant)
    if isinstance(expected, str):
        assert val.value in (expected, expected.replace("'", '"'))

    else:
        assert val.value == expected


@pytest.mark.parametrize(
    "code, expected",
    [
        ("x = True", True),
        ("x = False", False),
        ("x = None", None),
    ],
)
def test_constant_bool_none(parse_code, code, expected):
    ir = parse_code(code)
    c = ir.body[0].value
    assert isinstance(c, IRConstant)
    assert c.value == expected


def test_name(parse_code):
    ir = parse_code("x = y")
    name_node = ir.body[0].value
    assert isinstance(name_node, IRName)
    assert name_node.name == "y"


def test_attribute_chain(parse_code):
    ir = parse_code("x = a.b.c")
    val = ir.body[0].value
    assert isinstance(val, IRAttribute)
    assert val.attr == "c"

    mid = val.value
    assert isinstance(mid, IRAttribute)
    assert mid.attr == "b"

    inner = mid.value
    assert isinstance(inner, IRName)
    assert inner.name == "a"


def test_subscript(parse_code):
    ir = parse_code("x = arr[0]")
    sub = ir.body[0].value
    assert isinstance(sub, IRSubscript)

    sub_value = sub.value
    assert isinstance(sub_value, IRName)
    assert sub_value.name == "arr"

    sub_index = sub.index
    assert isinstance(sub_index, IRConstant)
    assert sub_index.value == 0


def test_subscript_multiple_indices(parse_code):
    ir = parse_code("x = a[1, 2]")
    sub = ir.body[0].value
    assert isinstance(sub, IRSubscript)
    assert isinstance(sub.index, IRTuple)
    assert len(sub.index.elements) == 2
    assert isinstance(sub.index.elements[0], IRConstant)
    assert sub.index.elements[0].value == 1
    assert isinstance(sub.index.elements[1], IRConstant)
    assert sub.index.elements[1].value == 2


def test_subscript_single_with_trailing_comma(parse_code):
    ir = parse_code("x = a[0,]")
    sub = ir.body[0].value
    assert isinstance(sub, IRSubscript)
    assert isinstance(sub.index, IRConstant)
    assert sub.index.value == 0


def test_subscript_three_indices(parse_code):
    ir = parse_code("x = a[1, 2, 3]")
    sub = ir.body[0].value
    assert isinstance(sub.index, IRTuple)
    assert len(sub.index.elements) == 3


def test_subscript_with_names(parse_code):
    ir = parse_code("x = dct[str, int]")
    sub = ir.body[0].value
    assert isinstance(sub.index, IRTuple)
    assert isinstance(sub.index.elements[0], IRName)
    assert sub.index.elements[0].name == "str"
    assert isinstance(sub.index.elements[1], IRName)
    assert sub.index.elements[1].name == "int"


def test_call_simple(parse_code):
    ir = parse_code("x = f()")
    call = ir.body[0].value
    assert isinstance(call, IRCall)

    func = call.func
    assert isinstance(func, IRName)
    assert func.name == "f"
    assert call.args == []
    assert call.kwargs == {}


def test_call_with_args(parse_code):
    ir = parse_code("x = f(1, b=2)")
    call = ir.body[0].value
    assert isinstance(call, IRCall)
    assert len(call.args) == 1

    arg0 = call.args[0]
    assert isinstance(arg0, IRConstant)
    assert arg0.value == 1

    assert "b" in call.kwargs
    kw_b = call.kwargs["b"]
    assert isinstance(kw_b, IRConstant)
    assert kw_b.value == 2


@pytest.mark.parametrize(
    "expr, op",
    [
        ("-a", "-"),
        ("not a", "not"),
    ],
)
def test_unary_op(parse_code, expr, op):
    ir = parse_code(f"x = {expr}")
    un = ir.body[0].value
    assert isinstance(un, IRUnaryOp)
    assert un.op == op


@pytest.mark.parametrize(
    "expr, op",
    [
        ("a + b", IRBinOpType.ADD),
        ("a - b", IRBinOpType.SUB),
        ("a * b", IRBinOpType.MUL),
        ("a / b", IRBinOpType.DIV),
        ("a // b", IRBinOpType.FLOORDIV),
        ("a % b", IRBinOpType.MOD),
        ("a ** b", IRBinOpType.POW),
        ("a == b", IRBinOpType.EQ),
        ("a != b", IRBinOpType.NE),
        ("a < b", IRBinOpType.LT),
        ("a > b", IRBinOpType.GT),
        ("a <= b", IRBinOpType.LE),
        ("a >= b", IRBinOpType.GE),
        ("a and b", IRBinOpType.AND),
        ("a or b", IRBinOpType.OR),
        ("a in b", IRBinOpType.IN),
        ("a not in b", IRBinOpType.NOT_IN),
        ("a is b", IRBinOpType.IS),
        ("a is not b", IRBinOpType.IS_NOT),
    ],
)
def test_binary_ops(parse_code, expr, op):
    ir = parse_code(f"x = {expr}")
    binop = ir.body[0].value
    assert isinstance(binop, IRBinOp)
    assert binop.op == op
    left = binop.left
    assert isinstance(left, IRName)
    assert left.name == "a"
    right = binop.right
    assert isinstance(right, IRName)
    assert right.name == "b"


def test_priority(parse_code):
    ir = parse_code("x = a + b * c")
    top = ir.body[0].value
    assert isinstance(top, IRBinOp)
    assert top.op == IRBinOpType.ADD

    right = top.right
    assert isinstance(right, IRBinOp)
    assert right.op == IRBinOpType.MUL


def test_ternary(parse_code):
    ir = parse_code("x = a if b else c")
    val = ir.body[0].value
    assert isinstance(val, IRIfExpr)

    test = val.test
    assert isinstance(test, IRName)
    assert test.name == "b"

    body = val.body
    assert isinstance(body, IRName)
    assert body.name == "a"

    orelse = val.orelse
    assert isinstance(orelse, IRName)
    assert orelse.name == "c"
