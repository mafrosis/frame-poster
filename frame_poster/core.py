import contextlib
import datetime
import math
import os
import subprocess
import shutil
import tempfile

import cv2
from PIL import Image, ImageStat

from . import printer

THUMBNAIL_SIZE = 240    # 1080p / 8
SECONDS_INCREMENT = 30
FRAMES_PER_ROW = 10


def extract_frame(movie_filepath, tmpdir, seconds):
    ts = datetime.timedelta(seconds=seconds)
    filename = '{}/output-{}.bmp'.format(tmpdir, seconds)

    subprocess.check_call(
        "ffmpeg -ss {} -i '{}' -frames:v 1 {} &>/dev/null".format(ts, movie_filepath, filename), shell=True
    )
    if os.path.exists(filename):
        return filename


def extract_movie_length(movie_filepath):
    # TODO this function is not robust; too much awk and parsing
    output = subprocess.check_output(
        "ffprobe '{}' 2>&1 | awk '/Duration/ {{print $2}}'".format(movie_filepath), shell=True
    ).decode('utf8')

    length = output.strip()[0:-4].format(':')
    parts = length.split(':')

    return datetime.timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2])).seconds


def doit(movie_filepath, thumbnail_width, seconds_increment, frames_per_row, output_filename, estimate=False):
    # get length of movie (for approximate progress bar)
    movie_length = extract_movie_length(movie_filepath)

    prntr = printer.CliPrinter()
    prntr.p('Processing {}'.format(os.path.basename(movie_filepath)))

    # in-memory storage for all frame thumbnails
    frames = []
    current_row = i = seconds = 0

    prntr.progressf(0, 1, movie_length)

    # discover bounds of crop rectangle (removes black borders etc)
    crop_rectangle = _get_crop_rectangle(movie_filepath)

    with make_temp_directory() as tmpdir:
        while True:
            # extract an image from the movie
            filename = extract_frame(movie_filepath, tmpdir, seconds)
            if filename is None:
                # NOTE end of movie
                break

            # load image into Pillow
            im = Image.open(filename)

            # convert to a thumbnail (we're assuming the image is always wider than tall)
            im.thumbnail((thumbnail_width, thumbnail_width))
            frames.append(im)

            # remove the source bitmap (for disk space)
            os.remove(filename)

            # when estimating we only need one frame
            if estimate:
                prntr.progressf(100, 1, 100)
                break

            # display a nice progress bar
            i += 1
            prntr.progressf(i, seconds_increment, movie_length)
            seconds += seconds_increment

        # end progress bar
        prntr.close()

    if estimate:
        # estimate final poster size and exit
        output_width = thumbnail_width * frames_per_row
        output_height = (frames[0].size[1] * movie_length / frames_per_row) + (round(frames[0].size[1] / 3) * ((movie_length / frames_per_row) + 1))

        prntr.p('Estimated image size is {}x{} pixels, or {:.2f}x{:.2f} cm at 300 dpi'.format(
            output_width, round(output_height), output_width / 300 * 2.54, output_height / 300 * 2.54
        ))
        return

    # rearrange frames into columns and rows
    frames_by_row = [[]]

    for im in frames:
        # store in frames array
        frames_by_row[current_row].append(im)

        # move down to next row
        if len(frames_by_row[current_row]) == frames_per_row:
            current_row += 1
            frames_by_row.append([])

    # interesting info
    prntr.p('Extracted {} frames'.format(len(frames)))

    # thumbnails will be the width specified, and height is based on the ratio
    thumbnail_height = frames[0].size[1]

    # image width is simple
    output_width = thumbnail_width * frames_per_row

    # image height is number of rows * height + black spacing between rows
    output_height = (thumbnail_height * len(frames_by_row)) + (round(thumbnail_height / 3) * (len(frames_by_row) + 1))

    # interesting info
    prntr.p('Output image is {}x{} pixels, or {:.2f}x{:.2f} cm at 300 dpi'.format(
        output_width, output_height, output_width / 300 * 2.54, output_height / 300 * 2.54
    ))

    # create the final output image
    output = Image.new('RGB', (output_width, output_height))

    x = y = 0

    # iterate all rows of frames
    for i in range(len(frames_by_row)):
        # set y co-ordinate for this row, including space between rows
        y = (i * thumbnail_height) + (round(thumbnail_height / 3) * (i + 1))

        # iterate frames in this row
        for j in range(frames_per_row):
            x = j * thumbnail_width

            try:
                # extract frame and paste into output image at co-ordinates
                output.paste(frames_by_row[i][j], (x, y))
            except IndexError:
                # end of frames
                break

    # handle relative and absolute output filepaths
    output_filename = os.path.abspath(output_filename)
    prntr.p('Output file written to {}'.format(output_filename))

    # write the output file
    output.save(output_filename, dpi=(300,300))


def _strip_intro_outro(frames):
    start_frame = 0
    end_frame = len(frames)

    # iterate from start of movie forwards, finding frame where brightness goes above threshold
    for i in range(10):
        if not _is_above_percieved_brightness(frames[i], 100):
            start_frame = i
        else:
            break

    # iterate from end of movie backwards, finding frame where brightness goes above threshold
    for i in reversed(range(len(frames)-10, len(frames))):
        if not _is_above_percieved_brightness(frames[i], 100):
            end_frame = i
        else:
            break

    # slice frames from start and end
    frames[:] = frames[start_frame:end_frame]


def _is_above_percieved_brightness(im, threshold=50):
    # http://stackoverflow.com/a/3498247/425050
    stat = ImageStat.Stat(im)
    r,g,b = stat.rms
    pbrightness = math.sqrt(0.241*(r**2) + 0.691+(g**2) + 0.068*(b**2))

    #print('{}  {}'.format(seconds, pbrightness))
    return (pbrightness >= threshold)


def _get_crop_rectangle(movie_filepath, prntr):
    thresholds = []
    seconds = 60
    i = 0

    # find black borders
    with make_temp_directory() as tmpdir:
        for i in range(40):
            # extract a frame 30 seconds into the movie
            filename = extract_frame(movie_filepath, tmpdir, seconds)

            # read image and convert to greyscale
            img = cv2.imread(filename)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            thresholds.append(gray)
            seconds += 60

            i += 1
            #prntr.progressf(i, progress_increment, movie_length)

    combined = thresholds[0]
    for t in thresholds[1:]:
        combined = cv2.addWeighted(combined, 0.5, t, 0.5, 0)

    cv2.imwrite('output.bmp', combined)
    import ipdb; ipdb.set_trace()
    _, thresh = cv2.threshold(combined, 5, 255, cv2.THRESH_BINARY)
    cv2.imwrite('output.bmp', thresh)
    import ipdb; ipdb.set_trace()

    # find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        x, y, w, h = cv2.boundingRect(contours[0])

        # write a cropped image
        cv2.imwrite('output.bmp', img[y:y+h, x:x+w])

    return (x, y, x+w, y+h)


@contextlib.contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(temp_dir)
