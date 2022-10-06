"""
Holds the necessary classes and function to load and mount a file system.
"""
import os
import contextlib
from abc import ABC, abstractmethod
from attr import define
from typing import List

from image_info.utils.mount import mount, mount_at

#pylint: disable=too-few-public-methods


@define
class FstabEntry:
    """
    Contain an extracted line of an fstab. Can be used to mount the file system.
    """
    uuid: str
    mountpoint: str
    fstype: str
    options: str

    @classmethod
    def read_fstab(cls, tree):
        """
        Read the content of /etc/fstab in the tree.

        Returns a Fstab object contaning an entry for each all uncommented lines
        read from the configuration file.
        """
        fstabs = []
        with contextlib.suppress(FileNotFoundError):
            #pylint: disable=unspecified-encoding
            with open(f"{tree}/etc/fstab") as file:
                result = sorted(
                    [line.split() for line in file
                        if line.strip() and not line.startswith("#")])
                for fstab_entry in result:
                    fstabs.append(
                        FstabEntry(
                            fstab_entry[0].split("=")[1].upper(),
                            fstab_entry[1],
                            fstab_entry[2],
                            fstab_entry[3].split(",")))
        if fstabs:
            # sort the fstab entries by the mountpoint
            fstabs.sort(key=lambda x: x.mountpoint)
            return fstabs
        return None


@define
class FileSystem:
    """
    A FileSystem can:
    - be mounted to search for an fstab
    - be mounted to a fstab location (provided the fstab_entry to refer to)
    """
    uuid: str
    device: str
    mntops: list

    def fstab(self) -> List[FstabEntry]:
        """
        Returns the fstab from the FileSystem if it exists.
        """
        with mount(self.device, self.mntops) as tree:
            if os.path.exists(f"{tree}/etc/fstab"):
                return FstabEntry.read_fstab(tree)
        return None

    def mount_root(self, options, context, _fstype) -> str:
        """
        mount the FileSystem as the root. """
        options = options if options else []
        mntops = options + self.mntops if self.mntops else options
        return context.enter_context(mount(self.device, mntops))

    def mount_at(self, context, options, mountpoint, fstype):
        """
        mount the FileSystem at a specific mountpoint
        """
        options = options if options else []
        mntops = options + self.mntops if self.mntops else options
        context.enter_context(
            mount_at(
                self.device,
                mountpoint,
                options=mntops,
                extra=["-t", fstype]))


#pylint: disable=too-few-public-methods
class FileSystemFactory(ABC):
    """
    A contract to implement in order to be considered a FileSystem generator
    """

    @abstractmethod
    def fsystems(self) -> List[FileSystem]:
        """
        Returns a list of FileSystem objects corresponding to the volume or
        subvolumes of a partition
        """


class FileSystemMounter:
    """
    A FileSystem object can mount the entire FS if it contains a FStab.
    """

    def __init__(self, partitions: List[FileSystemFactory]):
        """
        device: some partitions use the global device, others have already
        another one.
        """
        self.fss: List[FileSystem] = []
        # generate the fs mount values for each partition and volumes
        for partition in partitions:
            self.fss.extend(partition.fsystems())

    def get(self, uuid):
        """
        return a FileSystem by its uuid
        """
        for fsystem in self.fss:
            if fsystem.uuid == uuid:
                return fsystem
        return None

    def mount_all(self, context):
        """
        Find the FileSystem holding the FStab, extract it and mount all the
        FileSystems according to it.
        """
        for fsystem in self.fss:
            fstab = fsystem.fstab()
            if fstab:
                break

        root_tree = None
        for fstab_entry in fstab:
            fsystem = self.get(fstab_entry.uuid)
            if root_tree is None:
                # the first mount point should be root
                if fstab_entry.mountpoint != "/":
                    raise RuntimeError(
                        "The first mountpoint in sorted fstab entries is not '/'")
                root_tree = fsystem.mount_root(fstab_entry.options,
                                               context,
                                               fstab_entry.fstype)
            else:
                fsystem.mount_at(context,
                                 fstab_entry.options,
                                 f"{root_tree}{fstab_entry.mountpoint}",
                                 fstab_entry.fstype)

        if not root_tree:
            raise RuntimeError("The root filesystem tree is not mounted")
        return root_tree
