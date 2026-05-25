from plg_reader import (
    IRBinOp,
    IRBinOpType,
    IRCall,
    IRConstant,
    IRDecorator,
    IRFunctionDef,
    IRName,
    IRPass,
    IRReturn,
)


def test_empty_func(parse_code):
    ir = parse_code("def f(): pass")
    func = ir.body[0]
    assert isinstance(func, IRFunctionDef)
    assert func.name == "f"
    assert func.params == []
    body0 = func.body[0]
    assert isinstance(body0, IRPass)


def test_func_with_params(parse_code):
    ir = parse_code("def add(a, b=10): return a+b")
    func = ir.body[0]
    assert len(func.params) == 2
    a = func.params[0]
    assert a.name == "a"
    assert a.kind == "positional"
    assert a.default is None
    b = func.params[1]
    assert b.name == "b"
    b_default = b.default
    assert isinstance(b_default, IRConstant)
    assert b_default.value == 10
    ret = func.body[0]
    assert isinstance(ret, IRReturn)
    ret_val = ret.value
    assert isinstance(ret_val, IRBinOp)
    assert ret_val.op == IRBinOpType.ADD


def test_params_with_annotations(parse_code):
    ir = parse_code("def f(a: int, b: str = 'hello'): ...")
    func = ir.body[0]
    a = func.params[0]
    assert a.name == "a"
    a_annot = a.annotation
    assert isinstance(a_annot, IRName)
    assert a_annot.name == "int"
    b = func.params[1]
    assert b.name == "b"
    b_annot = b.annotation
    assert isinstance(b_annot, IRName)
    assert b_annot.name == "str"
    b_default = b.default
    assert isinstance(b_default, IRConstant)
    assert b_default.value == "'hello'"


def test_star_kw_args(parse_code):
    ir = parse_code("def f(a, *args, **kwargs): pass")
    func = ir.body[0]
    params = func.params
    assert params[0].name == "a"
    assert params[1].kind == "star_arg"
    assert params[1].name == "args"
    assert params[2].kind == "kw_arg"
    assert params[2].name == "kwargs"


def test_return_annotation(parse_code):
    ir = parse_code("def f() -> int: return 0")
    func = ir.body[0]
    returns = func.returns
    assert returns is not None
    assert isinstance(returns, IRName)
    assert returns.name == "int"


def test_decorator(parse_code):
    ir = parse_code("@dec\ndef f(): pass")
    func = ir.body[0]
    assert isinstance(func, IRFunctionDef)
    assert len(func.decorators) == 1
    decorator = func.decorators[0]
    assert isinstance(decorator, IRDecorator)
    dec_expr = decorator.expr
    assert isinstance(dec_expr, IRName)
    assert dec_expr.name == "dec"


def test_decorator_with_args(parse_code):
    ir = parse_code("@dec(1)\ndef f(): pass")
    func = ir.body[0]
    dec = func.decorators[0]
    assert isinstance(dec, IRDecorator)
    dec_expr = dec.expr
    assert isinstance(dec_expr, IRCall)
    call_func = dec_expr.func
    assert isinstance(call_func, IRName)
    assert call_func.name == "dec"
    arg0 = dec_expr.args[0]
    assert isinstance(arg0, IRConstant)
    assert arg0.value == 1
