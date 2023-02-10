# /usr/bin/env python3
import sys
import os
import argparse
import tempfile
import json
import subprocess
from typing import Dict, Optional, Set, Tuple


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


def load(path) -> Tuple[Dict, Set]:
    """
    Returns the image-info bits from the input path. If it exit an
    unwanted_tmpfiles_d in the file, return it also=.
    """
    c = None
    with open(path, "r") as f:
        c = json.load(f)
    # Supports raw image-info or DB entry
    unwanted_tmpfiles_d = set(c.get("unwanted_tmpfiles_d", []))
    if "image-info" in c:
        c = c["image-info"]
    return c, unwanted_tmpfiles_d


def diff(first, second, unwanted_tmpfiles_d: Set, visual):
    c1, unwanted_tmpfiles_d1 = load(first)
    c2, unwanted_tmpfiles_d2 = load(second)
    unwanted_tmpfiles_d.union(unwanted_tmpfiles_d1, unwanted_tmpfiles_d2)
    c1 = FilterImageInfo(c1, unwanted_tmpfiles_d).apply()
    c2 = FilterImageInfo(c2, unwanted_tmpfiles_d).apply()
    if not c1 or not c2:
        raise RuntimeError("empty image-info to diff")
    with tempfile.TemporaryDirectory() as d:
        f1 = os.path.join(d, "item1")
        f2 = os.path.join(d, "item2")
        try:
            with open(f1, 'w') as ff1:
                json.dump(c1, ff1, indent=4)

            with open(f2, 'w') as ff2:
                json.dump(c2, ff2, indent=4)

            p = subprocess.run(["diff", f1, f2],
                               check=False,
                               capture_output=True)
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
    return diff(args.files[0],
                args.files[1],
                set(args.unwanted_tmpfiles_d),
                args.visual_diff)


if __name__ == "__main__":
    sys.exit(main())
