{#
   This template extends the standard nbconvert markdown template in
   such a way that input and output cells are wrapped in custom <div>
   tags which are marked with the CSS classes "jupyterInputCell" and
   "jupyterOutputCell". This allows us to use our own custom styling
   for input and output cells. Note that this works because it is
   valid to use raw HTML in markdown.

   When converted to markdown, input cells are formatted using code
   blocks that use triple backticks, and these can be wrapped directly
   in a <div>.

   By contrast, output cells are by default formatted using simply
   an indented block (rather than triple backticks). Such an indented
   block cannot directly be wrapped in a <div> without losing the
   formatting. Therefore we first apply a custom Jinja filter to
   each line of the output cell which removes the indentation, and
   then surround the result with triple backticks and finally wrap
   this in the custom <div>.
#}

{% extends "markdown.tpl" %}

{% block header %}
{{ super() }}

<style>
.jupyterInputCell {
    background-color: #0000ff11;
}

.jupyterOutputCell {
    /* we don't apply any specific styles here but leave it as a placeholder */
}

/* Pretty Pandas Dataframes */
.dataframe {
    border: 0;
    font-size: smaller;
}

.dataframe tr {
    border: none;
    background: #ffffff;
}
.dataframe tr:nth-child(even) {
    background: #f5f5f5;
}
.dataframe tr:hover {
    background-color: #e1f5fe;
}

.dataframe thead th {
    background: #fff;
    border-bottom: 1px solid #aaa;
    font-weight: bold;
}
.dataframe th {
    border: none;
    padding-left: 10px;
    padding-right: 10px;
}

.dataframe td{
    /* background: #fff; */
    border: none;
    text-align: right;
    min-width:5em;
    padding-left: 10px;
    padding-right: 10px;
}
</style>
{% endblock header %}

{% block input_group %}
{{ super() | wrap_as_jupyter_input_cell }}
{% endblock input_group %}

{% block output_group %}
{{ super() | wrap_as_jupyter_output_cell }}
{% endblock output_group %}
