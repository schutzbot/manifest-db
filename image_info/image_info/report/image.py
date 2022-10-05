"""
This module defines the elements composing an Image:
    - ImageFormat
    - Bootloader
    - PartitionTable
"""

import json
from attr import define

from image_info.utils.process import subprocess_check_output
from image_info.report.report import ReportElement


@define(slots=False)
class ImageFormat(ReportElement):
    """
    Object initialed with at least 'type' initialized. 'type' value is a string
    representing the format of the image. In case the type is 'qcow2', the
    'compat' attribute is initialized with a string value representing the
    compatibility version of the 'qcow2' image.
    """
    flatten = True
    image_format: dict

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["image-format"])

    @classmethod
    def from_device(cls, device):
        """
        Read image format.

        """
        qemu = subprocess_check_output(
            ["qemu-img", "info", "--output=json", device],
            json.loads)
        ftype = qemu["format"]
        if ftype == "qcow2":
            compat = qemu["format-specific"]["data"]["compat"]
            return cls({
                "type": ftype,
                "compat": compat
            })
        return cls({"type": ftype})
