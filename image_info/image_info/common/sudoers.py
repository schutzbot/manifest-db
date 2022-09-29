"""
environment
"""
import os
import contextlib
import glob
from attr import define
from image_info.report.common import Common


@define(slots=False)
class Sudoers(Common):
    """
    Sudoers
    """
    flatten = True
    sudoers: dict

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        """
        Read uncommented lines from sudoers configuration file and /etc/sudoers.d
        This functions does not actually do much of a parsing, as sudoers file
        format grammar is a bit too much for our purpose.
        Any #include or #includedir directives are ignored by this function.

        Returns: dictionary with the keys representing names of read configuration
        files, /etc/sudoers and files from /etc/sudoers.d. Value of each key is
        a list of strings representing uncommented lines read from the configuration
        file.

        An example return value:
        {
            "/etc/sudoers": [
                "Defaults   !visiblepw",
                "Defaults    always_set_home",
                "Defaults    match_group_by_gid",
                "Defaults    always_query_group_plugin",
                "Defaults    env_reset",
                "Defaults    env_keep =  \"COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS\"",
                "Defaults    env_keep += \"MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE\"",
                "Defaults    env_keep += \"LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES\"",
                "Defaults    env_keep += \"LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE\"",
                "Defaults    env_keep += \"LC_TIME LC_ALL LANGUAGE LINGUAS _XKB_CHARSET XAUTHORITY\"",
                "Defaults    secure_path = /sbin:/bin:/usr/sbin:/usr/bin",
                "root\tALL=(ALL) \tALL",
                "%wheel\tALL=(ALL)\tALL",
                "ec2-user\tALL=(ALL)\tNOPASSWD: ALL"
            ]
        }
        """
        result = {}

        def _parse_sudoers_file(f):
            lines = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line[0] == "#":
                    continue
                lines.append(line)
            return lines

        with contextlib.suppress(FileNotFoundError):
            with open(f"{tree}/etc/sudoers") as f:
                lines = _parse_sudoers_file(f)
                if lines:
                    result["/etc/sudoers"] = lines

        sudoersd_result = {}
        for file in glob.glob(f"{tree}/etc/sudoers.d/*"):
            with open(file) as f:
                lines = _parse_sudoers_file(f)
                if lines:
                    result[os.path.basename(file)] = lines
        if sudoersd_result:
            result["/etc/sudoers.d"] = sudoersd_result

        if result:
            return cls(result)
        return None

    @classmethod
    def from_json(cls, json_o):
        sudoers = json_o.get("sudoers")
        if sudoers:
            return cls(sudoers)
        return None
