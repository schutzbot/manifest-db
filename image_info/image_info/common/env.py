"""
environment
"""
from attr import define
from image_info.utils.utils import parse_environment_vars
from image_info.report.common import Common


@define(slots=False)
class OsRelease(Common):
    """
    Lists the packages of the distribution
    """
    flatten = True
    os_release: list[str]

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        with open(f"{tree}/etc/os-release") as f:
            return cls(parse_environment_vars(f.read()))

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["os-release"])
