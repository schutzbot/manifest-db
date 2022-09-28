"""
Services
"""
import os
from attr import define
from image_info.report.common import Common
from image_info.utils.process import subprocess_check_output
from image_info.utils.utils import parse_unit_files
from image_info.utils.root import change_root


def read_services(tree, state):
    """
    Read the list of systemd services on the system in the given state.

    Returns: alphabetically sorted list of strings representing systemd services
    in the given state.
    The returned list may be empty.

    An example return value:
    [
        "arp-ethers.service",
        "canberra-system-bootup.service",
        "canberra-system-shutdown-reboot.service",
        "canberra-system-shutdown.service",
        "chrony-dnssrv@.timer",
        "chrony-wait.service"
    ]
    """
    services_state = subprocess_check_output(
        [
            "systemctl",
            f"--root={tree}",
            "list-unit-files"
        ],
        (lambda s: parse_unit_files(s, state))
    )

    # Since systemd v246, some services previously reported as "enabled" /
    # "disabled" are now reported as "alias". There is no systemd command, that
    # would take an "alias" unit and report its state as enabled/disabled
    # and could run on a different tree (with "--root" option).
    # To make the produced list of services in the given state consistent on
    # pre/post v246 systemd versions, check all "alias" units and append them
    # to the list, if their target is also listed in 'services_state'.
    if state != "alias":
        services_alias = subprocess_check_output(
            [
                "systemctl",
                f"--root={tree}",
                "list-unit-files"
            ],
            (lambda s: parse_unit_files(s, "alias"))
        )

        for alias in services_alias:
            # The service may be in one of the following places (output of
            # "systemd-analyze unit-paths", it should not change too often).
            unit_paths = [
                "/etc/systemd/system.control",
                "/run/systemd/system.control",
                "/run/systemd/transient",
                "/run/systemd/generator.early",
                "/etc/systemd/system",
                "/run/systemd/system",
                "/run/systemd/generator",
                "/usr/local/lib/systemd/system",
                "/usr/lib/systemd/system",
                "/run/systemd/generator.late"
            ]

            with change_root(tree):
                for path in unit_paths:
                    unit_path = os.path.join(path, alias)
                    if os.path.exists(unit_path):
                        real_unit_path = os.path.realpath(unit_path)
                        # Skip the alias, if there was a symlink cycle. When
                        # symbolic link cycles occur, the returned path will be
                        # one member of the cycle, but no guarantee is made
                        # about which member that will be.
                        if os.path.islink(real_unit_path):
                            continue

                        # Append the alias unit to the list, if its target is
                        # already there.
                        if os.path.basename(real_unit_path) in services_state:
                            services_state.append(alias)

    # deduplicate and sort
    services_state = list(set(services_state))
    services_state.sort()

    return services_state


@define(slots=False)
class ServicesEnabled(Common):
    """
    Lists the packages of the distribution
    """
    flatten = True
    services_enabled: list[str]

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        return cls(read_services(tree, "enabled"))

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["services-enabled"])


@define(slots=False)
class ServicesDisabled(Common):
    """
    Lists the packages of the distribution
    """
    flatten = True
    services_disabled: list[str]

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        return cls(read_services(tree, "disabled"))

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["services-disabled"])
