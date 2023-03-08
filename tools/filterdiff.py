# /usr/bin/env python3
import sys
import os
import argparse
import tempfile
import json
import subprocess
from typing import Dict, Optional, Set


class FilterImageInfo:
    """
    Filter specific fields in the image-info that can't be compared
    together.
    """

    def __init__(self, imi: Optional[Dict], to_remove_tmpfiles_d: Set) -> None:
        self.imi: Dict = imi if imi else {}
        self.to_remove_tmpfiles_d = to_remove_tmpfiles_d

    def _tmpfiles_d(self):
        """
        Remove certain files from the tpmfiles_d that have a tendency of having
        a non fixed content.
        """
        tmpfilesd = self.imi.get("tmpfiles.d")
        if tmpfilesd:
            for _, v in tmpfilesd.items():
                for trm in self.to_remove_tmpfiles_d:
                    if trm in v:
                        del v[trm]

    def _lvm2(self):
        """
        LVM2 partitions have a UUID that is not fixed. Replace the value
        upon comparison time.
        """
        partitions = self.imi.get("partitions")
        if partitions:
            for partition in partitions:
                if partition.get("fstype") == "LVM2_member":
                    partition["uuid"] = "2022-07-01-fixed-uuid"

    def _iso(self):
        """
        For isos, the partition UUID is the date of the build. Replace
        that with a fixed one for the comparison.
        """
        if ("image-format" in self.imi and "type" in self.imi["image-format"] and
                self.imi["image-format"]["type"] == "raw"):
            if "partitions" in self.imi:
                for partition in self.imi["partitions"]:
                    if "fstype" in partition:
                        if partition["fstype"] == "iso9660":
                            partition["uuid"] = "2022-07-01-fixed-uuid"

    def apply(self) -> Dict:
        self._iso()
        self._lvm2()
        self._tmpfiles_d()
        return self.imi


class ImageInfo:

    imi: Dict
    unwanted_tmpfiles_d: Set

    def __init__(self, imi: Dict, unwanted_tmpfiles_d: Set, do_filter=True) -> None:
        """
        parameters:
        -----------
        imi:                    the image-info json as a Dict
        unwanted_tmpfiles_d:    Set of files to filter out at comparison time
        """
        self.unwanted_tmpfiles_d = unwanted_tmpfiles_d
        self.imi = imi
        self.do_filter = do_filter

    @classmethod
    def from_file(cls, path):
        """
        Loads an ImageInfo object from a file on disk. Supports raw image-info
        json files and DB entries from the manifest-db repository.
        """
        with open(path, "r") as f:
            c = json.load(f)
        if "image-info" in c:
            # In the case the file is a DB entry, it can contain an image-info
            # and also a list of unwanted tmpfiles_d to filter out on comparison
            # time.
            return cls(c["image-info"], set(c.get("unwanted_tmpfiles_d", [])))
        # In the case of a raw image-info, just init it with an empty
        # unwanted_tmpfiles_d set.
        return cls(c, set())

    def diff(self, other, unwanted_tmpfiles_d: Set, verbose=False) -> bool:
        """
        Do perform a diff between this object and an other of the same type.


        parameters:
        -----------
        other:                  the other ImageInfo object to diff against
        unwanted_tmpfiles_d:    A list of tmpfiles_d to ignore
                                All the unwanted_tmpfiles_d found in the
                                ImageInfo to compare are unioned with the
                                unwanted_tmpfiles_d given as parameters.
        verbose:                True to get the diff command output on stdout
        """
        unwanted_tmpfiles_d = self.unwanted_tmpfiles_d.union(
            unwanted_tmpfiles_d,
            other.unwanted_tmpfiles_d)
        s = self.imi
        o = other.imi
        if self.do_filter:
            s = FilterImageInfo(self.imi, unwanted_tmpfiles_d).apply()
        if other.do_filter:
            o = FilterImageInfo(other.imi, unwanted_tmpfiles_d).apply()
        if ImageInfo.exec_diff(s, o, verbose):
            return True
        return False

    @staticmethod
    def exec_diff(imi1: Dict, imi2: Dict, visual: bool) -> int:
        """
        Write up the two dictionaries to temporary files and invoke `diff` as a
        subprocess command. Visual set to True to get the result of the diff
        command on stdout.
        """
        with tempfile.TemporaryDirectory() as d:
            f1 = os.path.join(d, "item1")
            f2 = os.path.join(d, "item2")
            try:
                with open(f1, 'w') as ff1:
                    json.dump(imi1, ff1, indent=4)

                with open(f2, 'w') as ff2:
                    json.dump(imi2, ff2, indent=4)

                p = subprocess.run(["diff", f1, f2],
                                   check=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
                if visual:
                    out = p.stdout.decode("utf-8")
                    for l in out.split("\n"):
                        print(l)
                return p.returncode
            finally:
                os.remove(f1)
                os.remove(f2)


def main():
    parser = argparse.ArgumentParser(description="osbuild image tests")
    parser.add_argument("files",
                        nargs=2,
                        help="files to diff, 2 required")
    parser.add_argument("--unwanted-tmpfiles-d",
                        nargs="+",
                        default=[],
                        help="List of unwanted files to get from tmpfiles_d")
    parser.add_argument(
        "--visual-diff",
        action="store_true",
        default=False,
        help="set to see the diff result"
    )
    args = parser.parse_args()

    imi1 = ImageInfo.from_file(args.files[0])
    imi2 = ImageInfo.from_file(args.files[1])

    return imi1.diff(imi2, set(args.unwanted_tmpfiles_d), args.visual_diff)


if __name__ == "__main__":
    sys.exit(main())
