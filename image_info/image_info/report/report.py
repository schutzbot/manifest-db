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
from attr import define, fields

from image_info.utils.utils import sanitize_name

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
                report[sanitize_name(type(element).__name__)] = asdict(element)
        return report

    def dump(self):
        """
        Prints out a raw report
        """
        json.dump(self.produce_report(), sys.stdout, sort_keys=True, indent=4)
        print()

#pylint: disable=[too-many-arguments, invalid-name]


def asdict(
    inst,
    recurse=True,
    afilter=None,
    dict_factory=dict,
    retain_collection_types=False,
    value_serializer=None,
):
    """
    Based on the asdict from attrs. The only diff is that it replaces the
    underscores in variable names and turns them into dashes for all te keys in
    the resulting dict.

    Return the ``attrs`` attribute values of *inst* as a dict.

    Optionally recurse into other ``attrs``-decorated classes.

    :param inst: Instance of an ``attrs``-decorated class.
    :param bool recurse: Recurse into classes that are also
        ``attrs``-decorated.
    :param callable filter: A callable whose return code determines whether an
        attribute or element is included (``True``) or dropped (``False``).  Is
        called with the `attr.Attribute` as the first argument and the
        value as the second argument.
    :param callable dict_factory: A callable to produce dictionaries from.  For
        example, to produce ordered dictionaries instead of normal Python
        dictionaries, pass in ``collections.OrderedDict``.
    :param bool retain_collection_types: Do not convert to ``list`` when
        encountering an attribute whose type is ``tuple`` or ``set``.  Only
        meaningful if ``recurse`` is ``True``.
    :param Optional[callable] value_serializer: A hook that is called for every
        attribute or dict key/value.  It receives the current instance, field
        and value and must return the (updated) value.  The hook is run *after*
        the optional *filter* has been applied.

    :rtype: return type of *dict_factory*

    :raise attr.exceptions.NotAnAttrsClassError: If *cls* is not an ``attrs``
        class.

    ..  versionadded:: 16.0.0 *dict_factory*
    ..  versionadded:: 16.1.0 *retain_collection_types*
    ..  versionadded:: 20.3.0 *value_serializer*
    """
    attrs = fields(inst.__class__)
    rv = dict_factory()

    for a in attrs:
        v = getattr(inst, a.name)
        if afilter is not None and not afilter(a, v):
            continue

        if value_serializer is not None:
            v = value_serializer(inst, a, v)

        if recurse is True:
            if has(v.__class__):
                rv[sanitize_name(a.name)] = asdict(
                    v,
                    True,
                    afilter,
                    dict_factory,
                    retain_collection_types,
                    value_serializer,
                )
            elif isinstance(v, (tuple, list, set, frozenset)):
                cf = v.__class__ if retain_collection_types is True else list
                rv[sanitize_name(a.name)] = cf(
                    [
                        _asdict_anything(
                            i,
                            afilter,
                            dict_factory,
                            retain_collection_types,
                            value_serializer,
                        )
                        for i in v
                    ]
                )
            elif isinstance(v, dict):
                df = dict_factory
                rv[sanitize_name(a.name)] = df(
                    (
                        _asdict_anything(
                            kk,
                            afilter,
                            df,
                            retain_collection_types,
                            value_serializer,
                        ),
                        _asdict_anything(
                            vv,
                            afilter,
                            df,
                            retain_collection_types,
                            value_serializer,
                        ),
                    )
                    for kk, vv in v.items()
                )
            else:
                rv[sanitize_name(a.name)] = v
        else:
            rv[sanitize_name(a.name)] = v
    return rv


def _asdict_anything(
    val,
    afilter,
    dict_factory,
    retain_collection_types,
    value_serializer,
):
    """
    ``asdict`` only works on attrs instances, this works on anything.
    """
    if getattr(val.__class__, "__attrs_attrs__", None) is not None:
        # Attrs class.
        rv = asdict(
            val,
            True,
            afilter,
            dict_factory,
            retain_collection_types,
            value_serializer,
        )
    elif isinstance(val, (tuple, list, set, frozenset)):
        cf = val.__class__ if retain_collection_types is True else list
        rv = cf(
            [
                _asdict_anything(
                    i,
                    afilter,
                    dict_factory,
                    retain_collection_types,
                    value_serializer,
                )
                for i in val
            ]
        )
    elif isinstance(val, dict):
        df = dict_factory
        rv = df(
            (
                _asdict_anything(
                    kk, afilter, df, retain_collection_types, value_serializer
                ),
                _asdict_anything(
                    vv, afilter, df, retain_collection_types, value_serializer
                ),
            )
            for kk, vv in val.items()
        )
    else:
        rv = val
        if value_serializer is not None:
            rv = value_serializer(None, None, rv)

    return rv


def has(cls):
    """
    Check whether *cls* is a class with ``attrs`` attributes.

    :param type cls: Class to introspect.
    :raise TypeError: If *cls* is not a class.

    :rtype: bool
    """
    return getattr(cls, "__attrs_attrs__", None) is not None
