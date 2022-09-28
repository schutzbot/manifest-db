"""
root related utils
"""
import os
import contextlib


@contextlib.contextmanager
def change_root(root):
    """
    Do a change root on the new root
    """
    real_root = os.open("/", os.O_RDONLY)
    try:
        os.chroot(root)
        yield None
    finally:
        os.fchdir(real_root)
        os.chroot(".")
        os.close(real_root)
