"""
This module defines the elements composing an Image:
    - ImageFormat
    - Bootloader
    - PartitionTable
"""

import json
import subprocess
import contextlib
from attr import define

from image_info.utils.mount import mount
from image_info.utils.process import subprocess_check_output
from image_info.report.report import ReportElement
from image_info.report.partition import (
    GenericPartition,
    ImagePartition)
from image_info.core.filesystem import FileSystemMounter


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


@ define(slots=False)
class PartitionTable(ReportElement):
    """
    Read information related to found partitions and partitioning table from
    the device.
        - 'partition-table' value is a string with the type of the partition
          table or 'None'.
        - 'partition-table-id' value is a string with the ID of the partition
          table or 'None'.
        - 'partitions' value is a list of dictionaries representing found
          partitions.
    """
    flatten = True  # the resulting json will be merged with the parent object
    partition_table: str
    partition_table_id: str
    partitions: list[GenericPartition]

    @ classmethod
    def from_json(cls, json_o):
        partition_table = json_o["partition-table"]
        partition_table_id = json_o["partition-table-id"]
        partitions = []
        for partition in json_o["partitions"]:
            if partition_table is None:
                partitions.append(GenericPartition.from_json(partition))
            else:
                partitions.append(ImagePartition.from_json(partition))
        return cls(partition_table, partition_table_id, partitions)

    @ classmethod
    def from_device(cls, device, loctl, context):
        """
        Loads a PartitionTable from the device
        """
        try:
            sfdisk = subprocess_check_output(
                ["sfdisk", "--json", device], json.loads)
        except subprocess.CalledProcessError:
            # This handles a case, when the device does contain a filesystem,
            # but there is no partition table.
            partition = GenericPartition()
            partition.read_generics(device)
            return cls(None, None, [partition])

        ptable = sfdisk["partitiontable"]
        assert ptable["unit"] == "sectors"
        is_dos = ptable["label"] == "dos"
        ssize = ptable.get("sectorsize", 512)

        partitions = []
        for i, partition in enumerate(ptable["partitions"]):
            partuuid = partition.get("uuid")
            if not partuuid and is_dos:
                # For dos/mbr partition layouts the partition uuid
                # is generated. Normally this would be done by
                # udev+blkid, when the partition table is scanned.
                # 'sfdisk' prefixes the partition id with '0x' but
                # 'blkid' does not; remove it to mimic 'blkid'
                table_id = ptable['id'][2:]
                partuuid = f"{table_id:.33s}-{i+1:02x}"

            partitions.append(ImagePartition(
                partition.get("bootable", False),
                partuuid,
                partition["start"] * ssize,
                partition["size"] * ssize,
                partition["type"]).explore(device, loctl, context))

        partitions.sort(key=lambda x: x.partuuid)
        return cls(ptable["label"], ptable["id"], partitions)

    def has_partition_table(self):
        """
        Returns true if the partition table is actually containing one. False
        would mean that it only contains a single partition in self.partitions.
        """
        return self.partition_table is not None

    @contextlib.contextmanager
    def mount(self, device, context):
        """
        If the object contains a partition table:
            - Mount every partitions from the entire filesystem. This function
              will loop through all the partitions of the partition table, check
              if they are LVM partitions or not, then find the fstab and mount
              them accordingly.
        If the object does not:
            - Mount the device as the tree
        Yield the mounted tree as a result
        """
        if self.has_partition_table():
            yield FileSystemMounter(self.partitions).mount_all(context)
        else:
            with mount(device) as tree:
                yield tree
