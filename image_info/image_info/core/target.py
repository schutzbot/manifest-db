"""
Target definitions.
A Target represent a kind of "image" to analyse. That could be a tarball, a
compressed target, a Directory, an Ostree repo or commit and finally and Image.
Each one has a specific way of being loaded and are defined here.
"""
from abc import ABC, abstractmethod


class Target(ABC):
    """
    Abstract class that defines the Target framework. Each child class being
    able to handle a specific kind of images.
    """

    def __init__(self, target):
        self.target = target

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
