from textwrap import dedent

import pytest
from sqltest import funcs


def test_func_unique(model):
    column = model.columns[0]
    actual_sql = funcs.unique(model, column)
    expected_sql = dedent(
        """\
        select
          count(*) as failures
        from (

          select
            foo,
            count(*) as records
          from dev.test_model
          group by foo
            having count(*) > 1

        )"""
    )
    assert actual_sql == expected_sql
