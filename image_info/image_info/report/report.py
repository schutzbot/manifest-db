"""
This module defines the report and report elements.
All the classes defined in the other files in this directory are inherited from
ReportElement and therefore must mandatory define a way to load from a JSON
chunk.
Also a ReportElement must be generated from an image at some point so we expect
that some kind of method to do so exists.
"""

import sys
import json
from abc import ABC, abstractmethod
from attr import define, asdict


#pylint: disable=too-few-public-methods


@define(slots=False)
class ReportElement(ABC):
    """
    A report element defining a subset of the image. The inherited class holds
    the keys for exploring the values it needs. A ReportElement can also be
    loaded from a json chunk. All inherited classes must define the from_json
    method in order to do so.
    """
    flatten = False

    @classmethod
    @abstractmethod
    def from_json(cls, json_o):
        """
        Instanciate this element from a json object
        """


class Report:
    """
    A report is used to produce a JSON with all the needed information on an
    image. Elements can be added to a Report to make it more precise. Elements
    must inherit from ReportElement.
    """

    def __init__(self):
        self._elements: list[ReportElement] = []

    def add_element(self, element):
        """
        Add an element to the list.
        """
        self._elements.append(element)

    def produce_report(self):
        """
        Loop through all the report elements and get them as JSON
        """
        report = {}
        for element in self._elements:
            if element.flatten:
                report.update(asdict(element))
            else:
                report[type(element).__name__] = asdict(element)
        return report

    def dump(self):
        """
        Prints out a raw report
        """
        json.dump(self.produce_report(), sys.stdout, sort_keys=True, indent=4)
        print()
