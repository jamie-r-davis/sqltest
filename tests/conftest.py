import pytest

from sqltest.models import Model


@pytest.fixture
def model():
    model_config = {
        "name": "test_model",
        "schema": "dev",
        "columns": [
            {"name": "foo", "tests": ["unique"]},
            {
                "name": "bar",
                "tests": [{"accepted_values": {"min_value": 1, "max_value": 10}}],
            },
        ],
    }
    return Model.from_obj(model_config)
