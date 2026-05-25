from plg_reader import IRConstant, IRDict, IRDictItem, IRList, IRSet, IRTuple


def test_list(parse_code):
    ir = parse_code("x = [1, 2]")
    lst = ir.body[0].value
    assert isinstance(lst, IRList)
    assert len(lst.elements) == 2
    e0 = lst.elements[0]
    assert isinstance(e0, IRConstant)
    assert e0.value == 1
    e1 = lst.elements[1]
    assert isinstance(e1, IRConstant)
    assert e1.value == 2


def test_tuple_explicit(parse_code):
    ir = parse_code("x = (1, 2)")
    tup = ir.body[0].value
    assert isinstance(tup, IRTuple)
    assert len(tup.elements) == 2


def test_set(parse_code):
    ir = parse_code("x = {1, 2}")
    s = ir.body[0].value
    assert isinstance(s, IRSet)
    assert len(s.elements) == 2


def test_dict(parse_code):
    ir = parse_code("x = {'a': 1, 'b': 2}")
    d = ir.body[0].value
    assert isinstance(d, IRDict)
    assert len(d.items) == 2
    item0 = d.items[0]
    assert isinstance(item0, IRDictItem)
    key0 = item0.key
    assert isinstance(key0, IRConstant)
    assert key0.value in ("'a'", '"a"')
    val0 = item0.value
    assert isinstance(val0, IRConstant)
    assert val0.value == 1


def test_empty_containers(parse_code):
    for expr, typ in [("[]", IRList), ("()", IRTuple), ("{}", IRDict)]:
        ir = parse_code(f"x = {expr}")
        val = ir.body[0].value
        assert isinstance(val, typ)
        if hasattr(val, "elements"):
            assert val.elements == []

        elif hasattr(val, "items"):
            assert val.items == []


def test_nested_containers(parse_code):
    ir = parse_code("x = [[1, 2], (3, 4)]")
    outer = ir.body[0].value
    assert isinstance(outer, IRList)
    inner_list = outer.elements[0]
    assert isinstance(inner_list, IRList)
    inner_tuple = outer.elements[1]
    assert isinstance(inner_tuple, IRTuple)
