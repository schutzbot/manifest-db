"""
Target definitions.
A Target represent a kind of "image" to analyse. That could be a tarball, a
compressed target, a Directory, an Ostree repo or commit and finally and Image.
Each one has a specific way of being loaded and are defined here.
"""
from abc import ABC, abstractmethod
import glob
import os
import sys

from image_info.report.common import import_plugins, find_commons
from image_info.utils.utils import sanitize_name
from image_info.report.report import Report


class Target(ABC):
    """
    Abstract class that defines the Target framework. Each child class being
    able to handle a specific kind of images.
    """

    def __init__(self, target):
        self.target = target
        import_plugins()

    @classmethod
    def match(cls, target):
        """
        returns True if the target can be handled by this class.
        """

    @abstractmethod
    def inspect(self):
        """
        explores the target and produces a JSON result
        """

    @classmethod
    def get(cls, target):
        """
        returns a specialized instance depending on the type of items archive we
        are dealing with.
        """
        raise NotImplemented("TODO")

    @classmethod
    def from_json(cls, json_o):
        raise NotImplemented("TODO")

    def inspect_commons(self, tree, is_ostree=False):
        """
        Adds all the common elements to the report
        """
        report = Report()
        if os.path.exists(f"{tree}/etc/os-release"):
            commons = find_commons()
            for common in commons:
                common_o = common.explore(tree, is_ostree)
                if common_o:
                    report.add_element(common_o)
        elif len(glob.glob(f"{tree}/vmlinuz-*")) > 0:
            pass
        else:
            print("EFI partition", file=sys.stderr)

    def commons_from_json(self, json_o):
        """
        Loads all the common elements from the input JSON
        """
        report = Report()
        commons = find_commons()
        for common in commons:
            c_json_name = sanitize_name(common.__name__)
            json_data = None
            if common.flatten:
                json_data = json_o
            else:
                json_data = json_o.get(c_json_name)
            if json_data:
                common_o = common.from_json(json_data)
                if common_o:
                    report.add_element(common_o)
            else:
                print(f"no json data for {c_json_name}")
