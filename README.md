## Sample Config

Configure your sql tests by creating yaml files for your models in the `models/` directory defining the tests for each of your models. While file names do not matter, it is best practice to create one file per model and name the file after the model, like so:

```
models/
  departments.yml
  customers.yml
```

Define your models like so:

```yaml
# table_1.yml

name: departments
schema: findw

# define any model-level tests 
tests:
  - unique_combination_of_columns:
      columns:
        - dept_id
        - dept_effdt


# define columns & column-level tests
columns:
  
  - name: dept_id
    tests:
      - not_null
      - regexp_like:
          expression: "^\\d{6}$"
  
  - name: dept_effdt
    tests:
      - not_null
      - accepted_range:
          min_value: date'1900-01-01'
          max_value: sysdate
          inclusive: true

  - name: dept_descr
    tests:
      - not_null
      - expression_is_true:
          expression: "length(dept_descr) <= 30"

  - name: dept_grp
    tests:
      - at_least_one

  ...
```


## Available Tests

### Unique
Check whether all values in a column are unique.

```yaml
tests:
  - unique
```

### Unique Combination of Columns
Checks whether values across a combination of columns are unique across the table. This is useful for testing composite keys.

```yaml
tests:
  - unique_combination_of_columns:
      columns:
        - emplid
        - acad_career
        - stdnt_car_nbr
```

### Expression is True
Checks whether the provided expression is true. This tests can be applied as either a model test or a column test.

```yaml
tests:
  - expression_is_true:
      expression: "created_dttm <= update_dttm"
```

To evaluate the expression against a constrained set of records, use the optional `where` parameter:

```yaml
tests:
  - expression_is_true:
      expression: "price = 150.50"
      where: "product_id = 123532"
```

### Relationships
Checks the referential integrity between two columns in the database:

```yaml
# model definition for a departments table

name: departments
schema: fin_dw
columns:
  - name: department_group
    tests:
      - relationships:
          to: fin_dw.department_groups
          field: group_id
```

### Value Equals
Checks whether the column equals the specified value for the provided `where` clause

```yaml
name: category
tests:
  # make sure product #12 is in the shoes category 
  - value_equals:
      where: "product_id = 12"
      value: "Shoes"
```
### Not Null
Verifies that column is not null.

### At Least One
Ensures that a column has at least one value and is not entirely null.

### Accepted Values

### Accepted Range

### RegExp Like
Tests column values to make sure they match the provided regex pattern.
```yaml

```

### UUID
Checks whether all values in a column match a uuid regex.

### Bit
