"""
Subscription manager
"""
import configparser
import contextlib
from attr import define
from image_info.report.common import Common


@define(slots=False)
class Rhsm(Common):
    """
    Rhsm
    """
    flatten = True
    rhsm: dict

    @classmethod
    def explore(cls, tree, _is_ostree=False):
        """
        Read configuration changes possible via org.osbuild.rhsm stage
        and in addition also the whole content of /etc/rhsm/rhsm.conf.

        Returns: returns dictionary with two keys - 'dnf-plugins' and 'rhsm.conf'.
        'dnf-plugins' value represents configuration of 'product-id' and
        'subscription-manager' DNF plugins.
        'rhsm.conf' value is a dictionary representing the content of the RHSM
        configuration file.
        The returned dictionary may be empty.

        An example return value:
        {
            "dnf-plugins": {
                "product-id": {
                    "enabled": true
                },
                "subscription-manager": {
                    "enabled": true
                }
            },
            "rhsm.conf": {
                "logging": {
                    "default_log_level": "INFO"
                },
                "rhsm": {
                    "auto_enable_yum_plugins": "1",
                    "baseurl": "https://cdn.redhat.com",
                    "ca_cert_dir": "/etc/rhsm/ca/",
                    "consumercertdir": "/etc/pki/consumer",
                    "entitlementcertdir": "/etc/pki/entitlement",
                    "full_refresh_on_yum": "0",
                    "inotify": "1",
                    "manage_repos": "0",
                    "package_profile_on_trans": "0",
                    "pluginconfdir": "/etc/rhsm/pluginconf.d",
                    "plugindir": "/usr/share/rhsm-plugins",
                    "productcertdir": "/etc/pki/product",
                    "repo_ca_cert": "/etc/rhsm/ca/redhat-uep.pem",
                    "repomd_gpg_url": "",
                    "report_package_profile": "1"
                },
                "rhsmcertd": {
                    "auto_registration": "1",
                    "auto_registration_interval": "60",
                    "autoattachinterval": "1440",
                    "certcheckinterval": "240",
                    "disable": "0",
                    "splay": "1"
                },
                "server": {
                    "hostname": "subscription.rhsm.redhat.com",
                    "insecure": "0",
                    "no_proxy": "",
                    "port": "443",
                    "prefix": "/subscription",
                    "proxy_hostname": "",
                    "proxy_password": "",
                    "proxy_port": "",
                    "proxy_scheme": "http",
                    "proxy_user": "",
                    "ssl_verify_depth": "3"
                }
            }
        }
        """

        result = {}

        # Check RHSM DNF plugins configuration and allowed options
        dnf_plugins_config = {
            "product-id": f"{tree}/etc/dnf/plugins/product-id.conf",
            "subscription-manager": f"{tree}/etc/dnf/plugins/subscription-manager.conf"
        }

        for plugin_name, plugin_path in dnf_plugins_config.items():
            with contextlib.suppress(FileNotFoundError):
                with open(plugin_path) as f:
                    parser = configparser.ConfigParser()
                    parser.read_file(f)
                    # only read "enabled" option from "main" section
                    with contextlib.suppress(configparser.NoSectionError, configparser.NoOptionError):
                        # get the value as the first thing, in case it raises an exception
                        enabled = parser.getboolean("main", "enabled")

                        try:
                            dnf_plugins_dict = result["dnf-plugins"]
                        except KeyError as _:
                            dnf_plugins_dict = result["dnf-plugins"] = {}

                        try:
                            plugin_dict = dnf_plugins_dict[plugin_name]
                        except KeyError as _:
                            plugin_dict = dnf_plugins_dict[plugin_name] = {}

                        plugin_dict["enabled"] = enabled

        with contextlib.suppress(FileNotFoundError):
            rhsm_conf = {}
            with open(f"{tree}/etc/rhsm/rhsm.conf") as f:
                parser = configparser.ConfigParser()
                parser.read_file(f)
                for section in parser.sections():
                    section_dict = {}
                    section_dict.update(parser[section])
                    if section_dict:
                        rhsm_conf[section] = section_dict

            result["rhsm.conf"] = rhsm_conf

        if result:
            return cls(result)
        return None

    @classmethod
    def from_json(cls, json_o):
        return cls(json_o["rhsm"])
