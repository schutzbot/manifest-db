"""
Selinux
"""
import glob
import re
import contextlib
import subprocess
from typing import Dict
try:
    from attr import define, field
except ImportError:
    from attr import s as define
    from attr import ib as field
from image_info.utils.process import subprocess_check_output
from image_info.utils.utils import parse_environment_vars
from image_info.report.common import Common


def read_selinux_ctx_mismatch(tree, is_ostree):
    """
    Read any mismatch in selinux context of files on the image.

    Returns: list of dictionaries as described below. If there
    are no mismatches between used and expected selinux context,
    then an empty list is returned.

    If the checked 'tree' is ostree, then the path '/etc' is
    excluded from the check. This is beause it is bind-mounted
    from /usr/etc and therefore has incorrect selinux context
    for its filesystem path.

    An example of returned value:
    [
        {
            "actual": "system_u:object_r:root_t:s0",
            "expected": "system_u:object_r:device_t:s0",
            "filename": "/dev"
        },
        {
            "actual": "system_u:object_r:root_t:s0",
            "expected": "system_u:object_r:default_t:s0",
            "filename": "/proc"
        }
    ]
    """
    result = []

    # The binary policy that should be used is on the image and has name "policy.X"
    # where the "X" is a number. There may be more than one policy files.
    # In the usual case, the policy with the highest number suffix should be used.
    policy_files = glob.glob(f"{tree}/etc/selinux/targeted/policy/policy.*")
    policy_files = sorted(policy_files, reverse=True)

    if policy_files:
        cmd = [
            "setfiles",
            "-r", f"{tree}",
            "-nvF",
            "-c", policy_files[0],  # take the policy with the highest number
            f"{tree}/etc/selinux/targeted/contexts/files/file_contexts",
            f"{tree}"
        ]

        if is_ostree:
            # exclude /etc from being checked when the tree is ostree, because
            # it is just bind-mounted from /usr/etc and has incorrect selinux
            # context for /etc path
            cmd.extend(["-e", f"{tree}/etc"])

        output = subprocess_check_output(cmd)

        # output are lines such as:
        # Would relabel /tmp/tmpwrozmb47/dev from system_u:object_r:root_t:s0 to system_u:object_r:device_t:s0\n
        setfiles_pattern = r"Would\s+relabel\s+(?P<filename>.+)\s+from\s+(?P<actual>.+)\s+to\s+(?P<expected>.+)"
        setfiles_re = re.compile(setfiles_pattern)

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            match = setfiles_re.match(line)
            # do not silently ignore changes of 'setfiles' output
            if not match:
                raise RuntimeError(
                    f"could not match line '{line}' with pattern '{setfiles_pattern}'")
            parsed_line = {
                "filename": match.group("filename")[len(tree):],
                "actual": match.group("actual"),
                "expected": match.group("expected")
            }
            result.append(parsed_line)

        # sort the list to make it consistent across runs
        result.sort(key=lambda x: x.get("filename"))

    return result


def read_selinux_conf(tree):
    """
    Read all uncommented key/values set in /etc/selinux/config.

    Returns: dictionary with key/values read from the configuration
    file.

    An example of returned value:
    {
        "SELINUX": "enforcing",
        "SELINUXTYPE": "targeted"
    }
    """
    with contextlib.suppress(FileNotFoundError):
        with open(f"{tree}/etc/selinux/config") as f:
            return parse_environment_vars(f.read())


@define(slots=False)
class Selinux(Common):
    """
    Selinux
    """
    flatten = True
    selinux: Dict = field()

    @classmethod
    def explore(cls, tree, is_ostree=False):
        """
        Read information related to SELinux.

        Returns: dictionary with two keys - 'policy' and 'context-mismatch'.
        'policy' value corresponds to the value returned by read_selinux_conf().
        'context-mismatch' value corresponds to the value returned by
        read_selinux_ctx_mismatch().
        The returned dictionary may be empty. Keys with empty values are omitted.

        An example return value:
        {
            "context-mismatch": [
                {
                    "actual": "system_u:object_r:root_t:s0",
                    "expected": "system_u:object_r:device_t:s0",
                    "filename": "/dev"
                },
                {
                    "actual": "system_u:object_r:root_t:s0",
                    "expected": "system_u:object_r:default_t:s0",
                    "filename": "/proc"
                }
            ],
            "policy": {
                "SELINUX": "permissive",
                "SELINUXTYPE": "targeted"
            }
        }
        """
        result = {}

        policy = read_selinux_conf(tree)
        if policy:
            result["policy"] = policy

        with contextlib.suppress(subprocess.CalledProcessError):
            ctx_mismatch = read_selinux_ctx_mismatch(tree, is_ostree)
            if ctx_mismatch:
                result["context-mismatch"] = ctx_mismatch
        if result:
            return cls(result)
        return None

    @classmethod
    def from_json(cls, json_o):
        selinux = json_o.get("selinux")
        if selinux:
            return cls(selinux)
        return None
