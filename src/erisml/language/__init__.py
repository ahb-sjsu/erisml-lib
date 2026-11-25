# ErisML is a modeling layer for governed, foundation-model-enabled agents
# Copyright (c) 2025 Andrew H. Bond
#
# Licensed under the MIT License. See LICENSE.txt at the root of this repository.
"""The ErisML language: source text to a typed AST, and the AST to objects that run.

    from erisml.language import parse_erisml, build_model, ethics_profile

    ast = parse_erisml(source)
    model = build_model(ast, instances={"Room": ["r1", "r2"]}, rules={...})
    profile = ethics_profile(ast.ethics)
"""

from .ast import ModelAST
from .compile import CompileError, build_model, ethics_profile, evaluate, norm_texts
from .parser import ParsingError, parse_erisml

__all__ = [
    "CompileError",
    "ModelAST",
    "ParsingError",
    "build_model",
    "ethics_profile",
    "evaluate",
    "norm_texts",
    "parse_erisml",
]
