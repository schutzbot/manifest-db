"""
Configuration files
"""
import contextlib
from attr import define
from image_info.report.common import Common


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
