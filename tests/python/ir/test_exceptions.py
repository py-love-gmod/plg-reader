from plg_reader import IRExceptHandler, IRName, IRPass, IRRaise, IRTry


def test_raise_simple(parse_code):
    ir = parse_code("raise ValueError")
    r = ir.body[0]
    assert isinstance(r, IRRaise)
    assert isinstance(r.exc, IRName)
    assert r.exc.name == "ValueError"
    assert r.cause is None


def test_raise_with_from(parse_code):
    ir = parse_code("raise e from orig")
    r = ir.body[0]
    assert isinstance(r.exc, IRName)
    assert r.exc.name == "e"
    assert isinstance(r.cause, IRName)
    assert r.cause.name == "orig"


def test_try_except(parse_code):
    ir = parse_code("try:\n    pass\nexcept:\n    pass")
    t = ir.body[0]
    assert isinstance(t, IRTry)
    assert isinstance(t.body[0], IRPass)
    assert len(t.handlers) == 1
    h = t.handlers[0]
    assert isinstance(h, IRExceptHandler)
    assert h.type is None
    assert h.name is None
    assert isinstance(h.body[0], IRPass)


def test_try_except_with_type_and_name(parse_code):
    ir = parse_code("try:\n    pass\nexcept ValueError as e:\n    pass")
    t = ir.body[0]
    h = t.handlers[0]
    assert isinstance(h.type, IRName)
    assert h.type.name == "ValueError"
    assert h.name == "e"


def test_try_except_else_finally(parse_code):
    code = "try:\n    pass\nexcept:\n    pass\nelse:\n    pass\nfinally:\n    pass"
    ir = parse_code(code)
    t = ir.body[0]
    assert isinstance(t, IRTry)
    assert len(t.orelse) == 1
    assert isinstance(t.orelse[0], IRPass)
    assert len(t.finalbody) == 1
    assert isinstance(t.finalbody[0], IRPass)


def test_raise_alone(parse_code):
    ir = parse_code("try:\n    raise\nexcept:\n    pass")
    r = ir.body[0].body[0]
    assert isinstance(r, IRRaise)
    assert r.exc is None
    assert r.cause is None
