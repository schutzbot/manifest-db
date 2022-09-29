"""
Configuration files
"""
import os
import glob
import contextlib
import yaml
from attr import define
from image_info.report.common import Common


def _read_glob_paths_with_parser(tree, glob_paths, parser_func):
    """
    Use 'parser_func' to read all files obtained by using all 'glob_paths'
    globbing patterns under the 'tree' path.

    The 'glob_paths' is a list string patterns accepted by glob.glob().
    The 'parser_func' function is expected to take a single string argument
    containing the absolute path to a configuration file which should be parsed.
    Its return value can be arbitrary representation of the parsed
    configuration.

    Returns: dictionary with the keys corresponding to directories, which
    contain configuration files mathing the provided glob pattern. Value of
    each key is another dictionary with keys representing each filename and
    values being the parsed configuration representation as returned by the
    provided 'parser_func' function.

    An example return value for dracut configuration paths and parser:
    {
        "/etc/dracut.conf.d": {
            "sgdisk.conf": {
                "install_items": " sgdisk "
            },
        },
        "/usr/lib/dracut/dracut.conf.d": {
            "xen.conf": {
                "add_drivers": " xen-netfront xen-blkfront "
            }
        }
    }
    """
    result = {}

    for glob_path in glob_paths:
        glob_path_result = {}

        files = glob.glob(f"{tree}{glob_path}")
        for file in files:
            config = parser_func(file)
            if config:
                filename = os.path.basename(file)
                glob_path_result[filename] = config

        if glob_path_result:
            checked_path = os.path.dirname(glob_path)
            result[checked_path] = glob_path_result

    return result


@define(slots=False)
class Authselect(Common):
    """
    AuthSelect
    """
    enabled_features: list
    profile_id: str

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        """
        Read authselect configuration.

        Returns: dictionary with two keys 'profile-id' and 'enabled-features'.
        - 'profile-id' value is a string representing the configured authselect
          profile.
        - 'enabled-features' value is a list of strings representing enabled
          features of the used authselect profile. In case there are no specific
          features enabled, the list is empty.
        """
        with contextlib.suppress(FileNotFoundError):
            #pylint: disable = unspecified-encoding
            with open(f"{tree}/etc/authselect/authselect.conf") as f:
                # the first line is always the profile ID
                # following lines are listing enabled features
                # lines starting with '#' and empty lines are skipped
                authselect_conf_lines = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line[0] == "#":
                        continue
                    authselect_conf_lines.append(line)
                if authselect_conf_lines:
                    return cls(authselect_conf_lines[1:],
                               authselect_conf_lines[0])
        return None

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["enabled-features"], json_o["profile-id"])


@define(slots=False)
class Chrony(Common):
    """
    Chrony
    """
    flatten = True
    chrony: dict

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        """
        Read specific directives from Chrony configuration. Currently parsed
        directives are:
        - 'server'
        - 'pool'
        - 'peer'
        - 'leapsectz'

        Returns: dictionary with the keys representing parsed directives from Chrony
        configuration. Value of each key is a list of strings containing arguments
        provided with each occurance of the directive in the configuration.
        """
        chrony = {}
        parsed_directives = ["server", "pool", "peer", "leapsectz"]
        with contextlib.suppress(FileNotFoundError):
            #pylint: disable = unspecified-encoding
            with open(f"{tree}/etc/chrony.conf") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # skip comments
                    if line[0] in ["!", ";", "#", "%"]:
                        continue
                    split_line = line.split()
                    if split_line[0] in parsed_directives:
                        try:
                            directive_list = chrony[split_line[0]]
                        except KeyError:
                            directive_list = chrony[split_line[0]] = []
                        directive_list.append(" ".join(split_line[1:]))
        if chrony:
            return cls(chrony)
        return None

    @classmethod
    def from_json(cls, json_o):
        chrony = json_o.get("chrony")
        if chrony:
            return cls(chrony)
        return None


@define(slots=False)
class CloudInit(Common):
    """
    CloudInit
    """
    flatten = True
    cloud_init: dict

    @staticmethod
    def read_cloud_init_config(config_path):
        """
        Read the specific cloud-init configuration file.

        Returns: dictionary representing the cloud-init configuration.

        An example return value:
        {
            "cloud_config_modules": [
                "mounts",
                "locale",
                "set-passwords",
                "rh_subscription",
                "yum-add-repo",
                "package-update-upgrade-install",
                "timezone",
                "puppet",
                "chef",
                "salt-minion",
                "mcollective",
                "disable-ec2-metadata",
                "runcmd"
            ],
            "cloud_final_modules": [
                "rightscale_userdata",
                "scripts-per-once",
                "scripts-per-boot",
                "scripts-per-instance",
                "scripts-user",
                "ssh-authkey-fingerprints",
                "keys-to-console",
                "phone-home",
                "final-message",
                "power-state-change"
            ],
            "cloud_init_modules": [
                "disk_setup",
                "migrator",
                "bootcmd",
                "write-files",
                "growpart",
                "resizefs",
                "set_hostname",
                "update_hostname",
                "update_etc_hosts",
                "rsyslog",
                "users-groups",
                "ssh"
            ],
            "disable_root": 1,
            "disable_vmware_customization": false,
            "mount_default_fields": [
                null,
                null,
                "auto",
                "defaults,nofail,x-systemd.requires=cloud-init.service",
                "0",
                "2"
            ],
            "resize_rootfs_tmp": "/dev",
            "ssh_deletekeys": 1,
            "ssh_genkeytypes": null,
            "ssh_pwauth": 0,
            "syslog_fix_perms": null,
            "system_info": {
            "default_user": {
                "gecos": "Cloud User",
                "groups": [
                    "adm",
                    "systemd-journal"
                ],
                "lock_passwd": true,
                "name": "ec2-user",
                "shell": "/bin/bash",
                "sudo": [
                    "ALL=(ALL) NOPASSWD:ALL"
                ]
            },
            "distro": "rhel",
            "paths": {
                "cloud_dir": "/var/lib/cloud",
                "templates_dir": "/etc/cloud/templates"
            },
            "ssh_svcname": "sshd"
            },
            "users": [
                "default"
            ]
        }
        """
        result = {}

        with contextlib.suppress(FileNotFoundError):
            with open(config_path) as f:
                config = yaml.safe_load(f)
                result.update(config)

        return result

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        """
        Read all cloud-init *.cfg files from a predefined list of paths and
        parse them.

        The searched paths are:
        - "/etc/cloud/cloud.cfg"
        - "/etc/cloud/cloud.cfg.d/*.cfg"

        Returns: dictionary as returned by '_read_glob_paths_with_parser()' with
        configuration representation as returned by 'read_cloud_init_config()'.
        """
        checked_globs = [
            "/etc/cloud/cloud.cfg",
            "/etc/cloud/cloud.cfg.d/*.cfg"
        ]

        cloud_init = _read_glob_paths_with_parser(
            tree, checked_globs, CloudInit.read_cloud_init_config)
        if cloud_init:
            return cls(cloud_init)
        return None

    @classmethod
    def from_json(cls, json_o):
        cloud_init = json_o.get("cloud-init")
        if cloud_init:
            return cls(cloud_init)
        return None
