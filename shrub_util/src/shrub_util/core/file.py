import os

import shrub_util.core.logging as logging


def file_exists(context, filename):
    return os.path.exists(filename) and not os.path.isdir(filename)


def file_read_file(context, filename):
    """Read the contents from a file
    Purpose: allow unit tests to stub file reads.
    Author: Mando van der Waarden
    Date: 2020-06-26

    """
    try:
        with open(filename, "r") as ifp:
            result = ifp.read()
    except Exception as ex:
        logging.get_logger().error(
            f"problem reading file {filename} in context {context}, {ex}", ex=ex
        )
        raise ex

    return result
