from functools import wraps
from textwrap import dedent, indent
from typing import Any, Callable

from sqltest.models import Model, ModelColumn

type SqlTestFunc = Callable[[Model, ModelColumn, ...], str]


def wrap_test_sql(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        raw_sql = fn(*args, **kwargs)
        formatted_test_sql = indent(dedent(raw_sql).strip(), " " * 2)
        sql = """\
            select
              count(*) as failures
            from (
            
            {test_sql}
            
            )"""
        final_sql = dedent(sql).format(test_sql=formatted_test_sql)
        return final_sql

    return wrapper


@wrap_test_sql
def unique(model: Model, column: ModelColumn, **kwargs) -> str:
    """Evaluates whether all values in a column are unique"""
    sql = f"""\
        select
          {column.name},
          count(*) as records
        from {model.schema}.{model.name}
        group by {column.name}
          having count(*) > 1"""
    return sql


@wrap_test_sql
def not_null(model: Model, column: ModelColumn, **kwargs) -> str:
    """Evaluates whether all values in a column are not null"""
    sql = f"""\
        select {column.name}
        from {model.schema}.{model.name}
        where
          {column.name} is null"""
    return sql


@wrap_test_sql
def accepted_values(
    model: Model, column: ModelColumn, values: list[Any], **kwargs
) -> str:
    """Evaluates whether the column contains any other than those passed in `values`"""

    # quote strings if `values` is a list of strings
    first_value = values[0]
    if isinstance(first_value, str):
        values_clause = ", ".join(f"'{v}'" for v in values)
    else:
        values_clause = ", ".join(values)

    sql = f"""\
        select {column.name}
        from {model.schema}.{model.name}
        where
          {column.name} is not null and
          {column.name} not in ({values_clause})"""

    return sql


@wrap_test_sql
def expression_is_true(
    model: Model,
    column: ModelColumn,
    expression: str,
    where: str | None = None,
    **kwargs,
) -> str:
    """Evaluates whether the passed sql expression is true"""
    sql = f"""\
        select *
        from {model.schema}.{model.name}
        where
          not({expression})"""

    # add the where clause, if provided
    if where:
        sql = f"""{dedent(sql)} and\n  {where}"""

    return sql


@wrap_test_sql
def relationships(
    model: Model,
    column: ModelColumn,
    to: str,
    field: str,
    where: str | None = None,
    **kwargs,
) -> str:
    """Checks referential integrity between the source column and a foreign key in another table."""
    sql = f"""\
        select a.{column.name}
        from {model.schema}.{model.name} a
          left join {to} b on a.{column.name} = b.{field}
        where
          a.{column.name} is not null and
          b.{field} is null"""

    if where:
        sql += f" and {where}"

    return sql


@wrap_test_sql
def unique_combination_of_columns(model: Model, columns: list[str], **kwargs) -> str:
    """Checks for uniqueness across one or more columns.

    This test is useful for testing compound primary keys.
    """
    column_list = ", ".join(columns)

    sql = f"""\
        select
          {column_list},
          count(*) as records
        from {model.schema}.{model.name}
        group by {column_list}
        having count(*) > 1
    """

    return sql


def at_least_one(model: Model, column: ModelColumn, **kwargs) -> str:
    sql = f"""\
        select
          case when records = 0 then 1 else 0 end as failures
        from (
        
          select
            count(*) as records
          from {model.schema}.{model.name}
          where
            {column.name} is not null
        
        )"""

    return dedent(sql)


@wrap_test_sql
def regexp_like(
    model: Model,
    column: ModelColumn,
    expression: str,
    flags: str | None = None,
    **kwargs,
) -> str:
    """Check whether a column matches a regex pattern"""
    sql = f"""
        select {column.name}
        from {model.schema}.{model.name}
        where
          {column.name} is not null and
          not(regexp_like({column.name}, '{expression}', '{flags or ''}'))
    """

    return sql


@wrap_test_sql
def uuid(model: Model, column: ModelColumn, **kwargs) -> str:
    """Checks whether column values match a uuid regex"""
    pattern = r"^[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}$"
    sql = f"""
        select {column.name}
        from {model.schema}.{model.name}
        where
          {column.name} is not null and
          not(regexp_like({column.name}, '{pattern}', 'i'))
    """
    return sql


@wrap_test_sql
def accepted_range(
    model: Model,
    column: ModelColumn,
    min_value: any = None,
    max_value: any = None,
    inclusive: bool = True,
    where: str | None = None,
) -> str:
    """Checks whether a column falls within an accepted range"""
    if min_value is None and max_value is None:
        raise ValueError("Specify at least a `min_value` or `max_value`")

    min_op = "<="
    max_op = ">="
    if inclusive:
        min_op = "<"
        max_op = ">"

    clauses = []

    if where:
        clauses.append(where)

    if min_value is not None:
        clauses.append(f"{column.name} {min_op} {min_value}")

    if max_value is not None:
        clauses.append(f"{column.name} {max_op} {max_value}")

    sql = f"""
        select {column.name}
        from {model.schema}.{model.name}
        where
          {column.name} is not null and
          {' or '.join(clauses)}
    """

    return sql


@wrap_test_sql
def bit(
    model: Model, column: ModelColumn, yes: str = "Y", no: str = "N", **kwargs
) -> str:
    """Checks whether a column has exclusively yes/no values."""
    if isinstance(yes, str):
        yes = f"'{yes}'"
    if isinstance(no, str):
        no = f"'{no}'"

    sql = f"""
        select {column.name}
        from {model.schema}.{model.name}
        where
          {column.name} is not null and
          {column.name} not in ({yes}, {no})
    """
    return sql


@wrap_test_sql
def value_equals(model: Model, column: ModelColumn, value: any, where: str) -> str:
    if isinstance(value, str):
        value = f"'{value}'"

    sql = f"""
        select {column.name}
        from {model.schema}.{model.name}
        where
          {where} and
          not({column.name} = {value})
    """

    return sql


@wrap_test_sql
def agg_value(
    model: Model,
    value: any,
    agg_expression: str,
    group_by: list[str],
    column: ModelColumn | None = None,
    agg_col: str | None = None,
    op: str = "=",
    where: str | None = None,
    **kwargs,
) -> str:
    """Checks whether an aggregated value matches the expected result"""

    if not agg_col and not column:
        raise ValueError("Must specify either `column` or `agg_col` for test condition")
    elif not agg_col:
        agg_col = column.name

    sql = f"""
      select
        {',\n  '.join(group_by)},
        {agg_expression} as agg_value
      from {model.schema}.{model.name}
      {{where}}
      group by 
        {', '.join(group_by)}
      having
        not({agg_expression} {op} {value})
    """

    if where:
        sql = sql.format(where=f"where {where}")
    else:
        sql = sql.format(where="")

    return sql
