import os
from enum import Enum

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


class FileLocationIteratorMode(Enum):
    MODE_FILES = 1
    MODE_FILE = 2


class FileLocationIterator:
    def __init__(self, location: str, mode: "" = FileLocationIteratorMode.MODE_FILE):
        self.location = location
        self.walker = None
        self.files = []
        self.root = None
        self.dir = None
        self.mode: FileLocationIteratorMode = mode
        self.walker = os.walk(self.location)

    def __next__(self):
        if self.mode == FileLocationIteratorMode.MODE_FILE:
            while len(self.files) == 0:
                self.root, self.dirs, self.files = next(self.walker)
            file = self.files[0]
            self.files = self.files[1:]
            return self.root, self.dirs, file
        else:
            return next(self.walker)
