"""
Network config
"""

import xml.etree.ElementTree
from attr import define
from image_info.report.common import Common
from image_info.utils.utils import parse_environment_vars


@define(slots=False)
class FirewallDefaultZone(Common):
    """
    FirewallDefaultZone
    """
    flatten = True
    firewall_default_zone: str

    @staticmethod
    def default_zone(tree):
        """
        Read the name of the default firewall zone

        Returns: a string with the zone name. If the firewall configuration doesn't
        exist, an empty string is returned.

        An example return value:
        "trusted"
        """
        try:
            with open(f"{tree}/etc/firewalld/firewalld.conf") as f:
                conf = parse_environment_vars(f.read())
                return conf["DefaultZone"]
        except FileNotFoundError:
            return ""

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        zone = FirewallDefaultZone.default_zone(tree)
        if zone:
            return cls(zone)
        else:
            return None

    @classmethod
    def from_json(cls, json_o):
        zone = json_o.get("firewall-default-zone")
        if zone:
            return cls(zone)
        return None


@define(slots=False)
class FirewallEnabled(Common):
    """
    FirewalEnabled
    """
    flatten = True
    firewall_enabled: dict

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        """
        Read enabled services from the configuration of the default firewall zone.

        Returns: list of strings representing enabled services in the firewall.
        The returned list may be empty.

        An example return value:
        [
            "ssh",
            "dhcpv6-client",
            "cockpit"
        ]
        """
        default = FirewallDefaultZone.default_zone(tree)
        if default == "":
            default = "public"

        r = []
        with contextlib.suppress(FileNotFoundError):
            try:
                root = xml.etree.ElementTree.parse(
                    f"{tree}/etc/firewalld/zones/{default}.xml").getroot()
            except FileNotFoundError:
                root = xml.etree.ElementTree.parse(
                    f"{tree}/usr/lib/firewalld/zones/{default}.xml").getroot()

            for element in root.findall("service"):
                r.append(element.get("name"))

        if r:
            return cls(r)

    @classmethod
    def from_json(cls, json_o):
        fwe = json_o.get("firewall-enabled")
        if fwe:
            return cls(fwe)
        return None
