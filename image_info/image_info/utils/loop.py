"""
Set of loopback utility functions
"""
import contextlib
import os
import errno

from osbuild.loop import Loop


@contextlib.contextmanager
def loop_create_device(ctl, f_desc, offset=None, sizelimit=None):
    """
    create a Linux loopback device and bounds f_desc on it.
    """
    while True:
        loop = Loop(ctl.get_unbound())
        try:
            loop.set_fd(f_desc)
        except OSError as err:
            loop.close()
            if err.errno == errno.EBUSY:
                continue
            raise err
        try:
            loop.set_status(offset=offset, sizelimit=sizelimit, autoclear=True)
        except BlockingIOError:
            loop.clear_fd()
            loop.close()
            continue
        break
    try:
        yield loop
    finally:
        loop.close()


@contextlib.contextmanager
def loop_open(ctl, image, *, offset=None, size=None):
    """
    open an image in a Linux loopback device.
    """
    with open(image, "rb") as file:
        f_desc = file.fileno()
        with loop_create_device(
                ctl, f_desc, offset=offset, sizelimit=size) as loop:
            yield os.path.join("/dev", loop.devname)
