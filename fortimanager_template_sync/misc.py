from jinja2 import Environment, meta


def find_all_vars(template_content):
    env = Environment()
    parsed_content = env.parse(template_content)

    return meta.find_undeclared_variables(parsed_content)
