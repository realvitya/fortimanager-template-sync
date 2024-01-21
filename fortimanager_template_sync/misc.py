"""Miscellaneous utilities."""
from jinja2 import Environment, meta


def find_all_vars(template_content: str) -> set:
    """
    Find all undeclared variables in the given template content.

    Args:
        template_content (str): The content of the template.

    Returns:
        list: A list of undeclared variables found in the template content.
    """
    env = Environment()
    parsed_content = env.parse(template_content)

    return meta.find_undeclared_variables(parsed_content)
