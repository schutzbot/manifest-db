"""
Target definitions.
A Target represent a kind of "image" to analyse. That could be a tarball, a
compressed target, a Directory, an Ostree repo or commit and finally and Image.
Each one has a specific way of being loaded and are defined here.
"""
from abc import ABC, abstractmethod
import glob
import os
import sys

from osbuild import loop

from image_info.report.common import import_plugins, find_commons
from image_info.utils.utils import sanitize_name
from image_info.report.report import Report
from image_info.report.image import ImageFormat


class Target(ABC):
    """
    Abstract class that defines the Target framework. Each child class being
    able to handle a specific kind of images.
    """

    def __init__(self, target):
        self.target = target
        self.report = Report()
        import_plugins()

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
        return ImageTarget(target)

    @classmethod
    def from_json(cls, json_o):
        if json_o.get("image-format"):
            return ImageTarget.from_json(json_o)
        return None

    def inspect_commons(self, tree, is_ostree=False):
        """
        Adds all the common elements to the report
        """
        if os.path.exists(f"{tree}/etc/os-release"):
            commons = find_commons()
            for common in commons:
                common_o = common.explore(tree, is_ostree)
                if common_o:
                    self.report.add_element(common_o)
        elif len(glob.glob(f"{tree}/vmlinuz-*")) > 0:
            pass
        else:
            print("EFI partition", file=sys.stderr)

    def commons_from_json(self, json_o):
        """
        Loads all the common elements from the input JSON
        """
        commons = find_commons()
        for common in commons:
            c_json_name = sanitize_name(common.__name__)
            json_data = None
            if common.flatten:
                json_data = json_o
            else:
                json_data = json_o.get(c_json_name)
            if json_data:
                common_o = common.from_json(json_data)
                if common_o:
                    self.report.add_element(common_o)
            else:
                print(f"no json data for {c_json_name}")


class ImageTarget(Target):
    """
    Handles an image.
    """

    def inspect(self):
        loctl = loop.LoopControl()
        image_format = ImageFormat.from_device(self.target)

    @classmethod
    def from_json(cls, json_o):
        imt = cls(None)
        imt.report.add_element(ImageFormat.from_json(json_o))
        return imt

    @ contextlib.contextmanager
    def open_target(self, ctl, image_format):
        """
        Opens the image in a loopback device. Apply qemu convertion if necessary
        """
        with tempfile.TemporaryDirectory(dir="/var/tmp") as tmp:
            if image_format.image_format["type"] != "raw":
                target = os.path.join(tmp, "image.raw")
                # a bug exists in qemu that causes the conversion to raw to fail
                # on aarch64 systems with a lot of cpus. A workaround is to use
                # a single coroutine to do the conversion. It doesn't slow down
                # the conversion by much, but it hangs about half the time
                # without the limit set. 😢
                # bug: https://bugs.launchpad.net/qemu/+bug/1805256
                if platform.machine() == 'aarch64':
                    subprocess.run(
                        ["qemu-img", "convert", "-m", "1", "-O", "raw",
                            self.target,
                            target], check=True
                    )
                else:
                    subprocess.run(
                        ["qemu-img", "convert", "-O", "raw", self.target,
                            target], check=True
                    )
            else:
                target = self.target

            size = os.stat(target).st_size

            with loop_open(ctl, target, offset=0, size=size) as dev:
                yield dev
