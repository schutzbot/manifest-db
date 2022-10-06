"""
Users
"""
from attr import define
from image_info.report.common import Common
from typing import List


@define(slots=False)
class Passwd(Common):
    """
    Passwd
    """
    flatten = True
    passwd: List[str]

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        with open(f"{tree}/etc/passwd") as f:
            return cls(sorted(f.read().strip().split("\n")))

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["passwd"])


@define(slots=False)
class Groups(Common):
    """
    Groups
    """
    flatten = True
    groups: List[str]

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        with open(f"{tree}/etc/group") as f:
            return cls(sorted(f.read().strip().split("\n")))

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["groups"])


@define(slots=False)
class PasswdSystem(Common):
    """
    Passwd
    """
    flatten = True
    passwd_system: List[str]

    @classmethod
    def explore(cls, tree, is_ostree=False):
        if not is_ostree:
            return None
        with open(f"{tree}/usr/lib/passwd") as f:
            return cls(sorted(f.read().strip().split("\n")))

    @classmethod
    def from_json(cls, json_o):
        config = json_o.get("passwd-system")
        if config:
            return cls(config)
        return None


@define(slots=False)
class GroupsSystem(Common):
    """
    Groups
    """
    flatten = True
    groups_system: List[str]

    @classmethod
    def explore(cls, tree, is_ostree=True):
        if not is_ostree:
            return None
        with open(f"{tree}/usr/lib/group") as f:
            return cls(sorted(f.read().strip().split("\n")))

    @classmethod
    def from_json(cls, json_o):
        config = json_o.get("groups-system")
        if config:
            return cls(config)
        return None
