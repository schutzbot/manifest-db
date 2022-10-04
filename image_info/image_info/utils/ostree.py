"""
ostree utils
"""
import sys
import subprocess


def run_ostree(*args, _input=None, _check=True, **kwargs):
    args = list(args) + [f'--{k}={v}' for k, v in kwargs.items()]
    print("ostree " + " ".join(args), file=sys.stderr)
    res = subprocess.run(["ostree"] + args,
                         encoding="utf-8",
                         stdout=subprocess.PIPE,
                         input=_input,
                         check=_check)
    return res
