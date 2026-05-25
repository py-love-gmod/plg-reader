from plg_reader import (
    IRAttribute,
    IRBreak,
    IRCall,
    IRConstant,
    IRContinue,
    IRDelete,
    IRFor,
    IRIf,
    IRName,
    IRPass,
    IRTuple,
    IRWhile,
    IRWith,
    IRWithItem,
)


def test_if_only(parse_code):
    ir = parse_code("if x:\n    pass")
    if_node = ir.body[0]
    assert isinstance(if_node, IRIf)
    test = if_node.test
    assert isinstance(test, IRName)
    assert test.name == "x"
    assert isinstance(if_node.body[0], IRPass)
    assert if_node.orelse == []


def test_if_else(parse_code):
    ir = parse_code("if x:\n    pass\nelse:\n    pass")
    if_node = ir.body[0]
    assert len(if_node.orelse) == 1
    else_node = if_node.orelse[0]
    assert else_node is not None


def test_if_elif_else(parse_code):
    code = "if a:\n    pass\nelif b:\n    pass\nelse:\n    pass"
    ir = parse_code(code)
    if_node = ir.body[0]
    assert isinstance(if_node, IRIf)
    assert len(if_node.orelse) == 2
    elif_node = if_node.orelse[0]
    assert isinstance(elif_node, IRIf)
    elif_test = elif_node.test
    assert isinstance(elif_test, IRName)
    assert elif_test.name == "b"
    assert not isinstance(if_node.orelse[1], IRIf)


def test_while(parse_code):
    ir = parse_code("while x:\n    pass")
    wh = ir.body[0]
    assert isinstance(wh, IRWhile)
    test = wh.test
    assert isinstance(test, IRName)
    assert test.name == "x"
    assert isinstance(wh.body[0], IRPass)


def test_for(parse_code):
    ir = parse_code("for i in range(10):\n    pass")
    fr = ir.body[0]
    assert isinstance(fr, IRFor)
    target = fr.target
    assert isinstance(target, IRName)
    assert target.name == "i"
    iter_node = fr.iter
    assert isinstance(iter_node, IRCall)
    func = iter_node.func
    assert isinstance(func, IRName)
    assert func.name == "range"
    arg0 = iter_node.args[0]
    assert isinstance(arg0, IRConstant)
    assert arg0.value == 10
    assert isinstance(fr.body[0], IRPass)


def test_for_tuple_unpack(parse_code):
    ir = parse_code("for k, v in d.items():\n    pass")
    fr = ir.body[0]
    assert isinstance(fr.target, IRTuple)
    tup = fr.target
    e0 = tup.elements[0]
    assert isinstance(e0, IRName)
    assert e0.name == "k"
    e1 = tup.elements[1]
    assert isinstance(e1, IRName)
    assert e1.name == "v"


def test_with(parse_code):
    ir = parse_code("with open('f') as f:\n    pass")
    w = ir.body[0]
    assert isinstance(w, IRWith)
    assert len(w.items) == 1
    item = w.items[0]
    assert isinstance(item, IRWithItem)
    opt_vars = item.optional_vars
    assert opt_vars is not None
    assert isinstance(opt_vars, IRName)
    assert opt_vars.name == "f"
    assert isinstance(w.body[0], IRPass)


def test_break_continue(parse_code):
    ir = parse_code("for i in range(10):\n    break\n    continue")
    body = ir.body[0].body
    assert isinstance(body[0], IRBreak)
    assert isinstance(body[1], IRContinue)


def test_delete(parse_code):
    ir = parse_code("del x")
    d = ir.body[0]
    assert isinstance(d, IRDelete)
    assert len(d.targets) == 1
    target = d.targets[0]
    assert isinstance(target, IRName)
    assert target.name == "x"


def test_delete_multiple(parse_code):
    ir = parse_code("del a, b.c")
    d = ir.body[0]
    assert len(d.targets) == 2
    t0 = d.targets[0]
    assert isinstance(t0, IRName)
    assert t0.name == "a"
    t1 = d.targets[1]
    assert isinstance(t1, IRAttribute)
    assert t1.attr == "c"
    assert isinstance(t1.value, IRName)
    assert t1.value.name == "b"
