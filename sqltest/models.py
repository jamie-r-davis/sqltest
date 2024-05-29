from dataclasses import dataclass, field
from pathlib import Path
from typing import Self, Any
import yaml


@dataclass
class ModelTest:
    """Dataclass for an individual test configuration"""

    name: str
    kwargs: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_obj(cls, obj: dict | str) -> Self:
        if isinstance(obj, dict):
            name = next(iter(obj.keys()))
            kwargs = obj[name]
        else:
            name = obj
            kwargs = {}

        return cls(name, kwargs)


@dataclass
class ModelColumn:
    name: str
    tests: list[ModelTest] = field(default_factory=list)

    def add_test(self, test: ModelTest):
        """Register a new test to the column"""
        self.tests.append(test)

    @classmethod
    def from_obj(cls, obj: dict) -> Self:
        try:
            name = obj["name"]
            tests = [ModelTest.from_obj(test) for test in obj.get("tests", [])]
        except Exception as e:
            print(f"Issue parsing model from: {obj}")
            raise e

        return cls(name, tests)


@dataclass
class Model:
    name: str
    schema: str
    tests: list[ModelTest] = field(default_factory=list)
    columns: list[ModelColumn] = field(default_factory=list)

    @classmethod
    def from_obj(cls, obj: dict) -> Self:
        name = obj["name"]
        schema = obj["schema"]
        tests = [ModelTest.from_obj(test) for test in obj.get("tests", [])]
        columns = [ModelColumn.from_obj(col) for col in obj.get("columns", [])]
        return cls(name=name, schema=schema, tests=tests, columns=columns)


@dataclass
class TestCase:
    model: Model
    column: ModelColumn | None
    test: ModelTest
    has_been_run: bool = False
    passed: bool | None = None
    result: Any = None
    error: Exception | None = None


@dataclass
class Source:
    name: str
    url: str
    kwargs: dict = field(default_factory=dict)


@dataclass
class Config:
    source: Source
    models: list[Model] = field(default_factory=list)

    @classmethod
    def from_obj(cls, obj: dict) -> Self:
        source = Source(**obj["source"])
        models = []

        models_dir = obj.get("models_dir", [])
        if isinstance(models_dir, str):
            models_dir = [models_dir]
        for path in models_dir:
            models += gather_models(path)
        if "models" in obj:
            models += [Model.from_obj(model) for model in obj.get("models", [])]
        return cls(source, models)

    @classmethod
    def from_yaml(cls, file_path: str | Path):
        with Path(file_path).open() as file:
            obj = yaml.safe_load(file)
            return cls.from_obj(obj)

    def select_model(self, name: str) -> Model:
        """Selects a model by name"""
        for model in self.models:
            if model.name.lower() == name.lower():
                return model
        raise ValueError(f'Could not find a model matching "{name}"')


def gather_models(models_dir: str | Path) -> list[Model]:
    """Gather models from models_dir"""
    models = []

    for yml_file in Path(models_dir).rglob("*.yml"):
        with yml_file.open("r") as f:
            model_data = yaml.safe_load(f)
            model = Model.from_obj(model_data)
            models.append(model)

    return models
