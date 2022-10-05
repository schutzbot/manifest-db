"""
Set of subprocess utility functions
"""
import sys
import subprocess


def subprocess_check_output(argv, parse_fn=None):
    """
    Encapsulate subprocess calls to pretty print the errors
    """
    try:
        output = subprocess.check_output(argv, encoding="utf-8")
    except subprocess.CalledProcessError as error:
        sys.stderr.write(f"--- Output from {argv}:\n")
        sys.stderr.write(error.stdout)
        sys.stderr.write("\n--- End of the output\n")
        raise

    return parse_fn(output) if parse_fn else output
