"""
Set of mounting utility functions
"""
import contextlib
import tempfile
import subprocess


@contextlib.contextmanager
def mount(device, options=None):
    """
    Mount the device in a newly created temporary directory as the mountpoint
    """
    options = options or []
    opts = ",".join(["ro"] + options)
    with tempfile.TemporaryDirectory() as mountpoint:
        subprocess.run(["mount", "-o", opts, device, mountpoint], check=True)
        try:
            yield mountpoint
        finally:
            subprocess.run(["umount", "--lazy", mountpoint], check=True)


@contextlib.contextmanager
def mount_at(device, mountpoint, options=None, extra=None):
    """
    Mount the device an already existing mountpoint
    """
    options = options or []
    extra = extra or []
    opts = ",".join(["ro"] + options)
    subprocess.run(["mount", "-o", opts] + extra +
                   [device, mountpoint], check=True)
    try:
        yield mountpoint
    finally:
        subprocess.run(["umount", "--lazy", mountpoint], check=True)
