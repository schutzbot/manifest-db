"""
This modules defines the different kind of partitions:
    - GenericPartition
    - ImagePartition
    - LvmPartition
        - LvmVolume
"""
import subprocess
from attr import field, define

from image_info.report.report import ReportElement
from image_info.utils.loop import loop_open
from image_info.utils.utils import parse_environment_vars
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
    bootable: bool
    partuuid: str
    start: int
    size: int
    type: str

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
        """
        # open the partition and read info
        dev = self.open(loctl, device, context)
        # update the partition information from the mounted device
        self.read_generics(dev)
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

    def fsystems(self):
        """
        Return a list of FileSystem objects, one for each partition contained in
        this partition.
        """
        if self.uuid and self.fstype:
            return [FileSystem(self.uuid.upper(), self.device, None)]
        return []
