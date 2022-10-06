"""
This modules defines the different kind of partitions:
    - GenericPartition
    - ImagePartition
    - LvmPartition
        - LvmVolume
"""
import subprocess
import contextlib
from collections import OrderedDict
from typing import Iterator
from typing import Iterator, Dict
try:
    from attr import define, field
except ImportError:
    from attr import s as define
    from attr import ib as field

from image_info.report.report import ReportElement
from image_info.utils.loop import loop_open
from image_info.utils.utils import parse_environment_vars
from image_info.utils.lvm import ensure_device_file, volume_group_for_device
from image_info.core.filesystem import FileSystem, FileSystemFactory


@define(slots=False)
class GenericPartition(ReportElement):
    """
    A Specialized Partition object can inherit from GenericPartition to gain the
    ability to "read" the corresponding partition on the device. Doing so will
    fill some attributes for the partition.
    Note that the fields aren't in the constructor for reason being that it
    might not be possible to now these values upon creation of the inherited
    object. Much often, these objects require a first discovery to know where to
    mount there partition in order to discover these details.
    """
    label: str = field(init=False, default=None)
    uuid: str = field(init=False, default=None)
    fstype: str = field(init=False, default=None)

    def update_generics(self, json_o):
        """
        Update the fields from a json object. Can be called by a Child class to
        update its super fields.
        """
        self.label = json_o["label"]
        self.uuid = json_o["uuid"]
        self.fstype = json_o["fstype"]

    @ classmethod
    def from_json(cls, json_o):
        obj = cls()
        obj.update_generics(json_o)
        return obj

    def read_generics(self, device):
        """
        Read block device attributes using 'blkid' and extend the passed
        'partition' dictionary.

        Returns: the 'partition' dictionary provided as an argument, extended
        with 'label', 'uuid' and 'fstype' keys and their values.
        """
        res = subprocess.run(["blkid", "-c", "/dev/null", "--output", "export",
                              device],
                             check=False, encoding="utf-8",
                             stdout=subprocess.PIPE)
        if res.returncode == 0:
            blkid = parse_environment_vars(res.stdout)
            self.label = blkid.get("LABEL")  # doesn't exist for mbr
            self.uuid = blkid.get("UUID")
            self.fstype = blkid.get("TYPE")

    def copy_from(self, other):
        """
        Copy the fields from another GenericPartition
        """
        self.label = other.label
        self.uuid = other.uuid
        self.fstype = other.fstype


@ define(slots=False)
class ImagePartition(GenericPartition, FileSystemFactory):
    """
    {
        "bootable": false,
        "partuuid": "64AF1EC2-0328-406A-8F36-83016E6DD858",
        "size": 1048576,
        "start": 1048576,
        "type": "21686148-6449-6E6F-744E-656564454649",
    }
    """
    bootable: bool = field()
    partuuid: str = field()
    start: int = field()
    size: int = field()
    type: str = field()

    @ classmethod
    def from_json(cls, json_o):
        obj = cls(json_o["bootable"], json_o["partuuid"],
                  json_o["start"], json_o["size"], json_o["type"])
        obj.update_generics(json_o)
        return obj

    def explore(self, device, loctl, context):
        """
        Explore the partition:
            - mount the device at the spot the partition is on
            - read the information found there
            - if the partition is an lvm one:
                - transform the partition as a LvmPartition
        """
        # open the partition and read info
        dev = self.open(loctl, device, context)
        # update the partition information from the mounted device
        self.read_generics(dev)
        # detect if the partition is an lvm partition, transform it if it is
        if self.is_lvm():
            return self.to_lvm_partition(dev, context)
        # pylint: disable=attribute-defined-outside-init
        self.device = dev
        return self

    def open(self, loctl, device, context):
        """
        Opens the partition and returns a device to access it
        """
        return context.enter_context(
            loop_open(
                loctl,
                device,
                offset=self.start,
                size=self.size))

    def is_lvm(self) -> bool:
        """
        Returns true if the partition is an LVM partition
        """
        return self.type.upper() in ["E6D6D379-F507-44C2-A23C-238F2A3DF928",
                                     "8E"]

    def to_lvm_partition(self, dev, context_manager):
        """
        Transform a simple image partition into an lvm one
        """
        return context_manager.enter_context(LvmPartition.discover_lvm(dev,
                                                                       self))

    def fsystems(self):
        """
        Return a list of FileSystem objects, one for each partition contained in
        this partition.
        """
        if self.uuid and self.fstype:
            return [FileSystem(self.uuid.upper(), self.device, None)]
        return []


@ define(slots=False)
class LvmVolume(GenericPartition):
    """
    Inheriting from GenericPartition a LvmVolume just keeps track of the
    information gathered by reading the device. The class brings the ability to
    obtain a FileSystem object out of the partition with the fs method in order
    to be mounted with special care.
    """

    def file_system(self):
        """
        return a FileSystem object having special mounting options
        """
        if self.fstype:
            mntopts = []
            # we cannot recover since the underlying loopback
            # device is mounted read-only but since we are using
            # the it through the device mapper the fact might
            # not be communicated and the kernel attempt a to a
            # recovery of the filesystem, which will lead to a
            # kernel panic
            if self.fstype in ("ext4", "ext3", "xfs"):
                mntopts = ["norecovery"]
            # the device attribute is set outside of the attrs context in order
            # to keep the value out of the generated dict by asdict()
            # pylint: disable=no-member
            return FileSystem(self.uuid.upper(), self.device, mntopts)
        return None


@ define(slots=False)
class LvmPartition(ImagePartition):
    """
    An lvm partition contains subvolumes that are stored as a list.
    """
    lvm: bool = field()
    lvm__vg: str = field()
    lvm__volumes: Dict[str, LvmVolume] = field()

    @ classmethod
    def from_json(cls, json_o):
        volumes = {}
        for k, val in json_o["lvm.volumes"].items():
            volumes[k] = LvmVolume.from_json(val)

        obj = cls(json_o["bootable"], json_o["partuuid"],
                  json_o["start"], json_o["size"], json_o["type"],
                  json_o["lvm"], json_o["lvm.vg"], volumes)
        obj.update_generics(json_o)
        return obj

    @ classmethod
    @ contextlib.contextmanager
    def discover_lvm(cls, dev, partition) -> Iterator:
        """
        discover all the volumes under the current partition
        """
        # find the volume group name for the device file
        vg_name = volume_group_for_device(dev)

        # activate it
        res = subprocess.run(["vgchange", "-ay", vg_name],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.PIPE,
                             check=False)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())

        try:
            # Find all logical volumes in the volume group
            cmd = [
                "lvdisplay", "-C", "--noheadings",
                "-o", "lv_name,path,lv_kernel_major,lv_kernel_minor",
                "--separator", ";",
                vg_name
            ]

            res = subprocess.run(cmd,
                                 check=False,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 encoding="UTF-8")

            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())

            data = res.stdout.strip()
            parsed = list(map(lambda l: l.split(";"), data.split("\n")))
            volumes = OrderedDict()

            for vol in parsed:
                vol = list(map(lambda v: v.strip(), vol))
                assert len(vol) == 4
                name, voldev, major, minor = vol
                ensure_device_file(voldev, int(major), int(minor))

                volumes[name] = LvmVolume()
                volumes[name].read_generics(voldev)
                if name.startswith("root"):
                    volumes.move_to_end(name, last=False)
                # setting this attribute outside of attrs makes the library
                # blind to it, so it will not show in the asdict() result, but
                # we still can use it
                # pylint: disable=attribute-defined-outside-init
                volumes[name].device = voldev
            lvm_partition = cls(
                partition.bootable,
                partition.partuuid,
                partition.start,
                partition.size,
                partition.type,
                True,
                vg_name,
                volumes)
            lvm_partition.copy_from(partition)
            yield lvm_partition

        finally:
            res = subprocess.run(["vgchange", "-an", vg_name],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.PIPE,
                                 check=False)
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())

    def fsystems(self):
        fsystems = []
        for _, volume in self.lvm__volumes.items():
            file_system = volume.file_system()
            if file_system:
                fsystems.append(file_system)
        return fsystems
