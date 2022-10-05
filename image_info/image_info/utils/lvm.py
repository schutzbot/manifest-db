"""
Lvm volumes utility functions
"""
import subprocess
import time
import os
import stat


def ensure_device_file(path: str, major: int, minor: int):
    """Ensure the device file with the given major, minor exists"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        os.mknod(path, 0o600 | stat.S_IFBLK, os.makedev(major, minor))


def volume_group_for_device(device: str) -> str:
    """
    Find the volume group that belongs to the device specified via `parent`
    """
    vg_name = None
    count = 0

    cmd = [
        "pvdisplay", "-C", "--noheadings", "-o", "vg_name", device
    ]

    while True:
        res = subprocess.run(cmd,
                             check=False,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding="UTF-8")

        if res.returncode == 5:
            if count == 10:
                raise RuntimeError("Could not find parent device")
            time.sleep(1*count)
            count += 1
            continue

        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())

        vg_name = res.stdout.strip()
        if vg_name:
            break

    return vg_name
