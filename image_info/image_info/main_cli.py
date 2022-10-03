"""
Entry points for the image info executables
"""
from os import walk
import argparse
import os
import json
import sys

from image_info.core.target import Target


def inspect():
    """
    Inspect an image
    """
    parser = argparse.ArgumentParser(description="Inspect an image")
    parser.add_argument("target", metavar="TARGET",
                        help="The file or directory to analyse",
                        type=os.path.abspath)

    args = parser.parse_args()
    target = Target.get(args.target)
    target.inspect()
    json.dump(
        target.report.produce_report(),
        sys.stdout,
        sort_keys=True,
        indent=2)


def loads():
    """
    Loasd an image-info JSON
    """
    parser = argparse.ArgumentParser(description="Inspect an image")
    parser.add_argument(
        "file",
        metavar="TARGET",
        help="The image-info file to load",
        type=os.path.abspath)
    parser.add_argument(
        "--list-dumpable",
        action="store_true",
        default=False,
        help="List all the things that can be dumped from this image-info file"
    )
    parser.add_argument(
        "--filter-dump",
        default=[],
        nargs='+',
        help="Filter what is dumped from this image info file")

    args = parser.parse_args()
    filenames = [args.file]
    if os.path.isdir(args.file):
        filenames = next(walk(args.file), (None, None, []))[2]

    for file in filenames:
        if os.path.isdir(args.file):
            file = os.path.join(args.file, file)
        with open(file, "r", encoding="utf-8") as f:
            content = json.load(f)["image-info"]
            if content:
                target = Target.from_json(content)
                if not target:
                    continue
                if args.list_dumpable:
                    target.report.list_dumpable()
                else:
                    if len(filenames) > 1:
                        print(f"{file}:")
                    target.report.dump(args.filter_dump)
