{% macro financial_numeric(precision=8) %}
    numeric(20, {{ precision }})
{% endmacro %}
