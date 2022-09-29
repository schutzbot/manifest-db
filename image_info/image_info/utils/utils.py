"""
Set of generic utility functions
"""

import re


def parse_unit_files(s, expected_state):
    r = []
    for line in s.split("\n")[1:]:
        try:
            unit, state, *_ = line.split()
        except ValueError:
            pass
        if state != expected_state:
            continue
        r.append(unit)

    return r


def parse_environment_vars(vrs):
    """
    Return all the env variables
    """
    res = {}
    for line in vrs.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line[0] == '#':
            continue
        key, value = line.split("=", 1)
        res[key] = value.strip('"')
    return res


def camel_case_to_snake_case(string):
    """
    Transforms a CamelCase to snake_case
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def snake_case_to_json(string):
    """
    transforms snake_case to snake-case, snake__case to snake.case, and
    snake_l_case to snake/case
    """
    return string.replace("_l_", "/").replace("__", ".").replace("_", "-")


def json_to_camel_case(string):
    """
    Transforms a json-key style string to a CamelCase style.
    """
    return ''.join(word.title() for word in string.split('-'))


def json_to_snake_case(string):
    """
    Transforms a json-key style string to a snake_case style.
    And json.key to json__key
    And json/key to json_l_key
    """
    return string.replace("-", "_").replace(".", "__").replace("/", "_l_")


def sanitize_name(name):
    """
    The json keys in the image-info have a specific formating except a few of
    them. Apply the necessary transformations here.
    """
    if name not in (
            "rpm_not_installed_docs",
            "sshd_config",
            "ssh_config",
    ):
        return snake_case_to_json(camel_case_to_snake_case(name))
    return name
