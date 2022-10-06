"""
This module defines the elements specific for OStree
"""

import functools
import os
import tempfile
import contextlib
from attr import define
from typing import List, Dict


from image_info.report.report import ReportElement
from image_info.utils.ostree import run_ostree


@define(slots=False)
class Type(ReportElement):
    """
    Ostree type
    """
    flatten = True
    type: str

    @classmethod
    def from_device(cls, device):
        if os.path.exists(os.path.join(device, "compose.json")):
            return cls("ostree/commit")
        if os.path.isdir(os.path.join(device, "refs")):
            return cls("ostree/repo")
        return None

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["type"])


@define(slots=False)
class Ostree(ReportElement):
    """
    Ostree element
    """
    repo: Dict
    refs: List

    @classmethod
    def from_device(cls, device):
        ostree = functools.partial(run_ostree, repo=device)
        repo = {
            "core.mode": ostree("config", "get", "core.mode").stdout.strip()
        }
        refs = ostree("refs").stdout.strip().split("\n")
        return cls(repo, refs)

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["repo"], json_o["refs"])

    @contextlib.contextmanager
    def mount(self, device):
        ostree = functools.partial(run_ostree, repo=device)
        resolved = {r: ostree("rev-parse", r).stdout.strip()
                    for r in self.refs}
        commit = resolved[self.refs[0]]

        with tempfile.TemporaryDirectory(dir="/var/tmp") as tmpdir:
            tree = os.path.join(tmpdir, "tree")
            ostree("checkout", "--force-copy", commit, tree)
            yield tree
