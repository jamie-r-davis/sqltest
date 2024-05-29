import pytest

from sqltest.models import Model


@pytest.fixture
def model():
    model_config = {
        "name": "test_model",
        "schema": "dev",
        "columns": [{"name": "foo", "tests": ["unique"]}],
    }
    return Model.from_obj(model_config)
