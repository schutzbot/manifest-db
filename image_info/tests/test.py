"""
unit tests
"""
import os
import json
import unittest
from image_info.core.target import Target


class TestBase(unittest.TestCase):

    def test_non_regression_json(self):
        current_dir = os.path.dirname(__file__)
        image_info_dir = os.path.dirname(current_dir)
        gitdir = os.path.dirname(image_info_dir)
        db_dir = os.path.join(gitdir, "manifest-db")

        filenames = next(os.walk(db_dir), (None, None, []))[2]

        self.maxDiff = None
        for file in filenames:
            path = os.path.join(db_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                print(f"Testing  {path}")
                content = json.load(f)["image-info"]
                if content:
                    target = Target.from_json(content)
                    if not target:
                        continue
                    report = target.report.produce_report()
                    self.assertEqual(report, content)
