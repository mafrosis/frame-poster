from __future__ import absolute_import
from __future__ import unicode_literals

import argparse
import sys

from . import __version__

class AppException(Exception):
    pass


def entrypoint():
    try:
        # setup and run argparse
        args = parse_command_line()

        # run main
        main(args)

    except AppException as e:
        sys.stderr.write('{}\n'.format(e))
        sys.stderr.flush()
        sys.exit(1)


def parse_command_line():
    parser = argparse.ArgumentParser(
        description='frame-poster'
    )

    # print the current version
    parser.add_argument(
        '-v', '--version', action='version',
        version='frame-poster {}'.format(__version__),
        help='Print the current frame-poster version')

    return parser.parse_args()


def main(args):
    pass