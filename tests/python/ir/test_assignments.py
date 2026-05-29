from plg_reader import (
    IRAnnotatedAssign,
    IRAssign,
    IRAttribute,
    IRBinOpType,
    IRConstant,
    IRDict,
    IRName,
    IRSubscript,
    IRTuple,
)


def test_simple_assign(parse_code):
    ir = parse_code("x = 1")
    assign = ir.body[0]
    assert isinstance(assign, IRAssign)
    assert len(assign.targets) == 1
    target = assign.targets[0]
    assert isinstance(target, IRName)
    assert target.name == "x"
    assert isinstance(assign.value, IRConstant)
    assert assign.value.value == 1
    assert not assign.is_aug


def test_aug_assign(parse_code):
    ir = parse_code("x += 1")
    assign = ir.body[0]
    assert assign.is_aug
    assert assign.aug_op == IRBinOpType.ADD
    assert isinstance(assign.value, IRConstant)
    assert assign.value.value == 1


def test_multi_target_assign(parse_code):
    ir = parse_code("x = y = 0")
    assign = ir.body[0]
    assert len(assign.targets) == 2
    assert isinstance(assign.targets[0], IRName)
    assert assign.targets[0].name == "x"
    assert isinstance(assign.targets[1], IRName)
    assert assign.targets[1].name == "y"


def test_tuple_unpack(parse_code):
    ir = parse_code("a, b = 1, 2")
    assign = ir.body[0]

    lhs_tuple = assign.targets[0]
    assert isinstance(lhs_tuple, IRTuple)
    assert len(lhs_tuple.elements) == 2
    assert isinstance(lhs_tuple.elements[0], IRName)
    assert lhs_tuple.elements[0].name == "a"
    assert isinstance(lhs_tuple.elements[1], IRName)
    assert lhs_tuple.elements[1].name == "b"

    rhs_tuple = assign.value
    assert isinstance(rhs_tuple, IRTuple)
    assert isinstance(rhs_tuple.elements[0], IRConstant)
    assert rhs_tuple.elements[0].value == 1
    assert isinstance(rhs_tuple.elements[1], IRConstant)
    assert rhs_tuple.elements[1].value == 2


def test_swap(parse_code):
    ir = parse_code("a, b = b, a")
    assign = ir.body[0]
    lhs = assign.targets[0]
    assert isinstance(lhs, IRTuple)
    rhs = assign.value
    assert isinstance(rhs, IRTuple)
    assert isinstance(lhs.elements[0], IRName)
    assert lhs.elements[0].name == "a"
    assert isinstance(lhs.elements[1], IRName)
    assert lhs.elements[1].name == "b"
    assert isinstance(rhs.elements[0], IRName)
    assert rhs.elements[0].name == "b"
    assert isinstance(rhs.elements[1], IRName)
    assert rhs.elements[1].name == "a"


def test_subscript_assign(parse_code):
    ir = parse_code("x[0] = 5")
    assign = ir.body[0]
    target = assign.targets[0]
    assert isinstance(target, IRSubscript)
    assert isinstance(target.value, IRName)
    assert target.value.name == "x"
    assert isinstance(target.index, IRConstant)
    assert target.index.value == 0


def test_annotated_assign_dict_subscript(parse_code):
    ir = parse_code("x: dict[str, int] = {}")
    node = ir.body[0]
    assert isinstance(node, IRAnnotatedAssign)
    ann = node.annotation
    assert isinstance(ann, IRSubscript)
    assert isinstance(ann.value, IRName)
    assert ann.value.name == "dict"
    assert isinstance(ann.index, IRTuple)
    assert len(ann.index.elements) == 2
    assert isinstance(ann.index.elements[0], IRName)
    assert ann.index.elements[0].name == "str"
    assert isinstance(ann.index.elements[1], IRName)
    assert ann.index.elements[1].name == "int"
    assert isinstance(node.value, IRDict)


def test_attr_assign(parse_code):
    ir = parse_code("obj.attr = 10")
    assign = ir.body[0]
    target = assign.targets[0]
    assert isinstance(target, IRAttribute)
    assert isinstance(target.value, IRName)
    assert target.value.name == "obj"
    assert target.attr == "attr"


def test_annotated_assign_simple(parse_code):
    ir = parse_code("x: int = 5")
    node = ir.body[0]
    assert isinstance(node, IRAnnotatedAssign)
    assert isinstance(node.target, IRName)
    assert node.target.name == "x"
    assert isinstance(node.annotation, IRName)
    assert node.annotation.name == "int"
    assert isinstance(node.value, IRConstant)
    assert node.value.value == 5


def test_annotated_assign_no_value(parse_code):
    ir = parse_code("x: int")
    node = ir.body[0]
    assert isinstance(node, IRAnnotatedAssign)
    assert isinstance(node.target, IRName)
    assert node.target.name == "x"
    assert isinstance(node.annotation, IRName)
    assert node.annotation.name == "int"
    assert node.value is None
