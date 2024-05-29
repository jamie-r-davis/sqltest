import pytest
from sqltest.models import ModelTest, ModelColumn, Model, Config


def test_model_test_from_string():
    obj = "unique"
    model = ModelTest.from_obj(obj)

    assert model.name == "unique"
    assert model.kwargs == {}


def test_model_test_from_obj():
    obj = {"expression_is_true": {"expression": "foo = bar"}}
    model = ModelTest.from_obj(obj)

    assert model.name == "expression_is_true"
    assert model.kwargs == {"expression": "foo = bar"}


def test_model_column_from_obj():
    obj = {
        "name": "column_a",
        "tests": ["unique", {"expression_is_true": {"foo = bar"}}],
    }
    model = ModelColumn.from_obj(obj)

    assert model.name == "column_a"
    assert len(model.tests) == 2


def test_model_from_obj():
    obj = {
        "name": "table_a",
        "schema": "dev",
        "columns": [
            {"name": "col_a", "tests": ["unique"]},
            {"name": "col_b", "tests": ["not_null"]},
        ],
    }
    model = Model.from_obj(obj)

    assert model.name == "table_a"
    assert model.schema == "dev"
    assert len(model.columns) == 2


def test_config_from_obj():
    obj = {
        "source": {"name": "foo", "url": "foodriver://foo.com:1234"},
        "models": [
            {"name": "model_a", "schema": "dev", "columns": [{"name": "foo"}]},
            {
                "name": "model_b",
                "schema": "dev",
                "columns": [{"name": "bar", "tests": ["unique"]}],
            },
        ],
    }
    config = Config.from_obj(obj)
    assert len(config.models) == 2
    assert config.models[0].name == "model_a"
