from plg_reader import IRClassDef, IRDecorator, IRFunctionDef, IRName, IRPass


def test_empty_class(parse_code):
    ir = parse_code("class A: pass")
    cls = ir.body[0]
    assert isinstance(cls, IRClassDef)
    assert cls.name == "A"
    assert cls.bases == []
    assert isinstance(cls.body[0], IRPass)


def test_class_with_bases(parse_code):
    ir = parse_code("class B(A, C): ...")
    cls = ir.body[0]
    assert len(cls.bases) == 2
    base0 = cls.bases[0]
    assert isinstance(base0, IRName)
    assert base0.name == "A"
    base1 = cls.bases[1]
    assert isinstance(base1, IRName)
    assert base1.name == "C"


def test_class_with_method(parse_code):
    ir = parse_code("class A:\n    def f(self): pass")
    cls = ir.body[0]
    method = cls.body[0]
    assert isinstance(method, IRFunctionDef)
    assert method.name == "f"


def test_class_decorator(parse_code):
    ir = parse_code("@dec\nclass A: pass")
    cls = ir.body[0]
    assert isinstance(cls, IRClassDef)
    assert len(cls.decorators) == 1
    decorator = cls.decorators[0]
    assert isinstance(decorator, IRDecorator)
    assert isinstance(decorator.expr, IRName)
    assert decorator.expr.name == "dec"
