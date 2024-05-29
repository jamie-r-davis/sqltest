from dataclasses import dataclass
import os
from textwrap import indent
from typing import Any, Sequence

import sqlalchemy as sa

from sqltest.models import Model, ModelColumn, ModelTest, Config
import sqltest.funcs as test_funcs
from sqltest.utils import Colors


@dataclass
class TestCase:
    model: Model
    column: ModelColumn | None
    test: ModelTest
    has_been_run: bool = False
    passed: bool | None = None
    result: Any = None
    error: Exception | None = None

    @property
    def sql(self) -> str:
        """The sql associated with the test case"""
        func = getattr(test_funcs, self.test.name)
        sql = func(model=self.model, column=self.column, **self.test.kwargs)
        return sql

    def __str__(self):
        if self.column:
            stem = f"{self.model.schema}.{self.model.name}.{self.column.name}: {self.test.name}"
        else:
            stem = f"{self.model.schema}.{self.model.name}: {self.test.name}"

        if self.has_been_run:
            if self.error is not None:
                msg = f"{stem} - {Colors.FAIL}ERROR{Colors.ENDC}"
            elif self.passed:
                msg = f"{stem} - {Colors.OKCYAN}PASSED{Colors.ENDC}"
            else:
                msg = f"{stem} - {Colors.FAIL}FAILED{Colors.ENDC}"
        else:
            msg = stem

        if self.test.kwargs:
            msg += f"\n{Colors.LIGHTGRAY} ↳ {self.test.kwargs}{Colors.ENDC}"

        return msg

    def report(self):
        msg = str(self)
        separator = "=" * 48

        if self.has_been_run:
            if self.error is not None:
                msg += (
                    f"{Colors.FAIL}\n"
                    f"{separator}\n"
                    f"{indent(str(self.error), ' '*4)}\n"
                    f"{separator}"
                    f"{Colors.ENDC}"
                )
            elif self.passed is False:
                msg += (
                    f"{Colors.FAIL}\n"
                    f"{separator}\n"
                    f"{indent(self.sql, ' ' * 4)}\n"
                    f"{separator}"
                    f"{Colors.ENDC}"
                )

        return msg


class TestRunner:
    def __init__(self, config: Config):
        self.config = config
        self._engine = None

    @property
    def engine(self) -> sa.Engine:
        if self._engine is None:
            url = self.config.source.url
            if url.startswith("$"):
                url = os.environ[url[1:]]
            self._engine = sa.create_engine(url)
        return self._engine

    def run_test(self, test_case: TestCase):
        with self.engine.connect() as db:
            try:
                result = db.exec_driver_sql(test_case.sql).fetchone()
            except Exception as e:
                test_case.has_been_run = True
                test_case.error = e
                test_case.passed = False
            else:
                test_case.result = result
                test_case.passed = result.failures == 0
                test_case.has_been_run = True

    def gather_test_cases(self, models: Sequence[str] | None = None) -> list[TestCase]:
        test_cases = []

        if models:
            models_to_test = list(
                filter(lambda x: x.name in models, self.config.models)
            )
        else:
            models_to_test = self.config.models

        for model in models_to_test:
            for test in model.tests:
                test_case = TestCase(model=model, column=None, test=test)
                test_cases.append(test_case)
            for column in model.columns:
                for test in column.tests:
                    test_case = TestCase(model, column, test)
                    test_cases.append(test_case)
        return test_cases

    def run(self, models: Sequence[str] | None = None):
        tested = 0
        passed = 0
        failed = 0
        errors = 0

        test_cases = self.gather_test_cases(models)

        for test_case in test_cases:
            self.run_test(test_case)

            print(test_case.report())

            if test_case.has_been_run:
                tested += 1
                if test_case.error:
                    errors += 1
                elif test_case.passed:
                    passed += 1
                else:
                    failed += 1

        separator = "+" * 79
        run_status = "Passed" if all(x.passed for x in test_cases) else "Failed"
        run_stats = f"Tested: {tested:,} - Passed: {passed:,} - Failed: {failed:,} - Errors: {errors:,}"
        color = Colors.OKCYAN if run_status == "Passed" else Colors.FAIL

        print(separator)
        print(f"{color}{run_status}{Colors.ENDC}")
        print(run_stats)

    def check_source(self):
        """Tests whether the data source connection is working"""
        with self.engine.connect() as db:
            pass
