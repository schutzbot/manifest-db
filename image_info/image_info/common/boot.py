"""
environment
"""
import os
import glob
import contextlib
from attr import define
from typing import List
from image_info.utils.utils import parse_environment_vars
from image_info.report.common import Common


def read_boot_entries(boot_dir):
    """
    Read boot entries.

    Returns: list of dictionaries representing configured boot entries.

    An example return value:
    [
        {
            "grub_arg": "--unrestricted",
            "grub_class": "kernel",
            "grub_users": "$grub_users",
            "id": "rhel-20210429130346-0-rescue-c116920b13f44c59846f90b1057605bc",
            "initrd": "/boot/initramfs-0-rescue-c116920b13f44c59846f90b1057605bc.img",
            "linux": "/boot/vmlinuz-0-rescue-c116920b13f44c59846f90b1057605bc",
            "options": "$kernelopts",
            "title": "Red Hat Enterprise Linux (0-rescue-c116920b13f44c59846f90b1057605bc) 8.4 (Ootpa)",
            "version": "0-rescue-c116920b13f44c59846f90b1057605bc"
        },
        {
            "grub_arg": "--unrestricted",
            "grub_class": "kernel",
            "grub_users": "$grub_users",
            "id": "rhel-20210429130346-4.18.0-305.el8.x86_64",
            "initrd": "/boot/initramfs-4.18.0-305.el8.x86_64.img $tuned_initrd",
            "linux": "/boot/vmlinuz-4.18.0-305.el8.x86_64",
            "options": "$kernelopts $tuned_params",
            "title": "Red Hat Enterprise Linux (4.18.0-305.el8.x86_64) 8.4 (Ootpa)",
            "version": "4.18.0-305.el8.x86_64"
        }
    ]
    """
    entries = []
    for conf in glob.glob(f"{boot_dir}/loader/entries/*.conf"):
        with open(conf) as f:
            entries.append(dict(line.strip().split(" ", 1) for line in f))

    return sorted(entries, key=lambda e: e["title"])


@define(slots=False)
class BootEnvironment(Common):
    """
    BootEnvironment
    """
    flatten = True
    boot_environment: List[str]

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        if os.path.exists(f"{tree}/boot") and len(os.listdir(f"{tree}/boot")) > 0:
            with contextlib.suppress(FileNotFoundError):
                with open(f"{tree}/boot/grub2/grubenv") as f:
                    return cls(parse_environment_vars(f.read()))
        return None

    @classmethod
    def from_json(cls, json_o):
        config = json_o.get("boot-environment")
        if config:
            return cls(config)
        return None


@define(slots=False)
class Bootmenu(Common):
    """
    Bootmenu
    """
    flatten = True
    bootmenu: List[str]

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        if os.path.exists(f"{tree}/boot") and len(os.listdir(f"{tree}/boot")) > 0:
            return cls(read_boot_entries(f"{tree}/boot"))
        return None

    @classmethod
    def from_json(cls, json_o):
        config = json_o.get("bootmenu")
        if config or config == []:  # legacy requires even an empty array in the JSON
            return cls(config)
