import argparse
import os
import sys

from . import __version__
from .core import doit, THUMBNAIL_SIZE, SECONDS_INCREMENT, FRAMES_PER_ROW

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
        help='Print the current frame-poster version'
    )

    parser.add_argument(
        'movie_file',
        help='The movie file to process into a poster'
    )

    parser.add_argument(
        '-E', '--estimate', action='store_true',
        help="Don't create a poster; just estimate its final size"
    )
    parser.add_argument(
        '-w', '--thumbnail-width', default=THUMBNAIL_SIZE, type=int,
        help='The width of each thumbnail in the output image (default is {}px)'.format(THUMBNAIL_SIZE)
    )
    parser.add_argument(
        '-s', '--seconds-between-frames', default=SECONDS_INCREMENT, type=int,
        help='The number of seconds between each frame capture (default is {})'.format(SECONDS_INCREMENT)
    )
    parser.add_argument(
        '-f', '--frames-per-row', default=FRAMES_PER_ROW, type=int,
        help='The number of frames per row in the output image (default is {})'.format(FRAMES_PER_ROW)
    )
    parser.add_argument(
        '-O', '--output-name', default='output.bmp',
        help='The output filename (default is output.bmp)'
    )

    args = parser.parse_args()

    if not os.path.isfile(args.movie_file):
        parser.error('File {} does not exist'.format(args.movie_file))

    return args


def main(args):
    doit(
        args.movie_file,
        args.thumbnail_width,
        args.seconds_between_frames,
        args.frames_per_row,
        args.output_name,
        estimate=args.estimate,
    )
