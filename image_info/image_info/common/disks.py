"""
Disks
"""
import contextlib
from typing import List
try:
    from attr import define, field
except ImportError:
    from attr import s as define
    from attr import ib as field
from image_info.report.common import Common


@define(slots=False)
class Fstab(Common):
    """
    Lists the packages of the distribution
    """
    flatten = True
    fstab: List[str] = field()

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        """
        Read the content of /etc/fstab.

        Returns: list of all uncommented lines read from the configuration file
        represented as a list of values split by whitespaces.
        The returned list may be empty.

        An example return value:
        [
            [
                "UUID=6d066eb4-e4c1-4472-91f9-d167097f48d1",
                "/",
                "xfs",
                "defaults",
                "0",
                "0"
            ]
        ]
        """
        result = []
        with contextlib.suppress(FileNotFoundError):
            with open(f"{tree}/etc/fstab") as f:
                result = sorted(
                    [line.split() for line in f if line.strip() and not line.startswith("#")])
        if result:
            return cls(result)
        return None

    @classmethod
    def from_json(cls, json_o):
        fstab = json_o.get("fstab")
        if fstab:
            return cls(fstab)
        return None
