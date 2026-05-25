from plg_reader import IRImport


def test_import_simple(parse_code):
    ir = parse_code("import os")
    assert len(ir.imports) == 1
    imp = ir.imports[0]
    assert isinstance(imp, IRImport)
    assert imp.modules == ["os"]
    assert imp.names == ["os"]
    assert not imp.is_from
    assert imp.level == 0


def test_import_dotted(parse_code):
    ir = parse_code("import os.path")
    imp = ir.imports[0]
    assert imp.modules == ["os.path"]
    assert imp.names == ["os.path"]


def test_import_as(parse_code):
    ir = parse_code("import os.path as path")
    imp = ir.imports[0]
    assert imp.modules == ["os.path"]
    assert imp.names == [("os.path", "path")]


def test_from_import(parse_code):
    ir = parse_code("from os import path")
    imp = ir.imports[0]
    assert imp.is_from
    assert imp.modules == ["os"]
    assert imp.names == ["path"]


def test_from_import_as(parse_code):
    ir = parse_code("from os.path import join as j")
    imp = ir.imports[0]
    assert imp.is_from
    assert imp.modules == ["os.path"]
    assert imp.names == [("join", "j")]


def test_relative_import(parse_code):
    ir = parse_code("from . import module")
    imp = ir.imports[0]
    assert imp.level == 1
    assert imp.modules == []
    assert imp.names == ["module"]


def test_multiple_imports(parse_code):
    ir = parse_code("import os, sys")
    modules = []
    names = []
    for imp in ir.imports:
        modules.extend(imp.modules)
        names.extend(imp.names)

    assert "os" in modules
    assert "sys" in modules
    assert "os" in names
    assert "sys" in names
