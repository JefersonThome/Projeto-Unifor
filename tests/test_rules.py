from src.pipeline import typed_expression


def test_score_is_double():
    assert "DOUBLE" in typed_expression("NT_GER")


def test_course_code_is_integer():
    assert "BIGINT" in typed_expression("CO_CURSO")


def test_questionnaire_is_preserved_as_text():
    assert "CAST" not in typed_expression("QE_I08")

