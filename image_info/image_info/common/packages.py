"""
Packages
"""
import os
import subprocess
from attr import define
from image_info.report.common import Common
from image_info.utils.process import subprocess_check_output


@define(slots=False)
class Packages(Common):
    """
    Lists the packages of the distribution
    """
    flatten = True
    packages: list[str]

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        """
        Read NVRs of RPM packages installed on the system.

        Returns: sorted list of strings representing RPM packages installed
        on the system.
        """
        cmd = ["rpm", "--root", tree, "-qa"]
        if os.path.exists(os.path.join(tree, "usr/share/rpm")):
            cmd += ["--dbpath", "/usr/share/rpm"]
        elif os.path.exists(os.path.join(tree, "var/lib/rpm")):
            cmd += ["--dbpath", "/var/lib/rpm"]
        packages = subprocess_check_output(cmd, str.split)
        return cls(list(sorted(packages)))

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["packages"])


@define(slots=False)
class RpmVerify(Common):
    """
    Read the output of 'rpm --verify'.
    """
    changed: dict
    missing: list

    @classmethod
    def explore(cls, tree, is_ostree=False):
        """
        Read the output of 'rpm --verify'.

        Returns: dictionary with two keys 'changed' and 'missing'.
        - 'changed' value is a dictionary with the keys representing modified
          files from installed RPM packages and values representing types of
          applied modifications.
        - 'missing' value is a list of strings prepresenting missing values
          owned by installed RPM packages.
        """
        if is_ostree:
            return None
        # cannot use `rpm --root` here, because rpm uses passwd from the host to
        # verify user and group ownership:
        #   https://github.com/rpm-software-management/rpm/issues/882
        rpm = subprocess.Popen(["chroot", tree, "rpm", "--verify", "--all"],
                               stdout=subprocess.PIPE, encoding="utf-8")

        changed = {}
        missing = []
        for line in rpm.stdout:
            # format description in rpm(8), under `--verify`
            attrs = line[:9]
            if attrs == "missing  ":
                missing.append(line[12:].rstrip())
            else:
                changed[line[13:].rstrip()] = attrs

        # ignore return value, because it returns non-zero when it found changes
        rpm.wait()
        return cls(changed, sorted(missing))

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["changed"], json_o["missing"])


@define(slots=False)
class RpmNotInstalledDocs(Common):
    """
    Read the output of 'rpm --verify'.
    """
    flatten = True
    rpm_not_installed_docs: list

    @classmethod
    def explore(cls, tree, is_ostree=False):
        """
        Gathers information on documentation, which is part of RPM packages,
        but was not installed.

        Returns: list of documentation files, which are normally a part of the
        installed RPM packages, but were not installed (e.g. due to using
        '--excludedocs' option when executing 'rpm' command).
        """
        # check not installed Docs (e.g. when RPMs are installed with
        # --excludedocs)
        not_installed_docs = []
        cmd = ["rpm", "--root", tree, "-qad", "--state"]
        if os.path.exists(os.path.join(tree, "usr/share/rpm")):
            cmd += ["--dbpath", "/usr/share/rpm"]
        elif os.path.exists(os.path.join(tree, "var/lib/rpm")):
            cmd += ["--dbpath", "/var/lib/rpm"]
        output = subprocess_check_output(cmd)
        for line in output.splitlines():
            if line.startswith("not installed"):
                not_installed_docs.append(line.split()[-1])

        if not_installed_docs:
            return cls(not_installed_docs)
        return None

    @classmethod
    def from_json(cls, json_o):
        data = json_o.get("rpm_not_installed_docs")
        if data:
            return cls(data)
        return None
