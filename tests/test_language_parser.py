import pytest

from erisml.language.ast import AgentDecl

VALID_MODEL = (
    "environment Home {\n"
    "  objects: Room;\n"
    "  state:\n"
    "    occupied: bool;\n"
    "}\n"
    "\n"
    "agent Robot {\n"
    "  capabilities: move;\n"
    "}\n"
)


def test_parse_erisml_returns_model_ast_for_minimal_model() -> None:
    from erisml.language.parser import parse_erisml

    model = parse_erisml(VALID_MODEL)

    assert model.environment.name == "Home"
    assert model.agents[0].name == "Robot"


def test_type_expr_rejects_unexpected_transform_items() -> None:
    from erisml.language.parser import ASTBuilder, ParsingError

    with pytest.raises(ParsingError, match="Invalid type expression"):
        ASTBuilder().type_expr([])


def test_model_rejects_missing_environment() -> None:
    from erisml.language.parser import ASTBuilder, ParsingError

    agent = AgentDecl(name="Robot", capabilities=["move"])

    with pytest.raises(ParsingError, match="Model must have an environment"):
        ASTBuilder().model([agent])


def test_parse_erisml_rejects_invalid_transformed_ast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from erisml.language import parser

    class InvalidASTBuilder:
        def transform(self, tree: object) -> object:
            return tree

    monkeypatch.setattr(parser, "ASTBuilder", InvalidASTBuilder)

    with pytest.raises(parser.ParsingError, match="ModelAST"):
        parser.parse_erisml(VALID_MODEL)
