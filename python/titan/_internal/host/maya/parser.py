from __future__ import absolute_import

from contextlib import contextmanager
import json
import re

from titan.logger import get_logger, log_execution_time

LOGGER_NAME = "titan.host.maya.parser"


@contextmanager
def _restore_handle_position(handle):
    """A context manager to restore the position of a file handle after
    reading from it."""
    offset = handle.tell()
    yield
    handle.seek(offset)


class FileInfoExtractor(object):
    """This class provides a set of methods to extract file info from Maya
    binary and ASCII files."""

    ASCII_FILE_INFO = "fileInfo"
    BINARY_FILE_INFO = b"FINF"
    BINARY_FILE_HEADER = b"FOR8"

    @classmethod
    @log_execution_time("titan.host.maya.parser")
    def get_file_info(cls, file_path):
        """Return a list of file info objects from the given file path. This
        method will check if the file is a Maya binary or ASCII file and
        extract the file info accordingly."""
        # Check if this is a Maya binary
        log = get_logger(LOGGER_NAME)
        log.debug("Opening %s", file_path)
        with open(file_path, "rb") as handle:
            if cls._peek(handle, len(cls.BINARY_FILE_HEADER)) == cls.BINARY_FILE_HEADER:
                log.trace(">> Extracting from Maya Binrary")
                return cls._extract_file_info_binary(handle)
        # Do Maya ASCII extraction instead
        with open(file_path, "r") as handle:
            log.trace(">> Extracting from Maya ASCII")
            return cls._extract_file_info_ascii(handle)

    @classmethod
    def _extract_file_info_ascii(cls, handle):
        """Extract file info from a Maya ASCII file. This method will read
        the file line by line and extract the file info from the fileInfo
        lines."""
        found_file_info = False
        file_infos = []
        line = handle.readline()
        while line:
            if line.startswith(cls.ASCII_FILE_INFO):
                file_infos.append(FileInfo.from_ascii(line))
                if not found_file_info:
                    found_file_info = True
            elif found_file_info:
                break
            line = handle.readline().strip()
        return file_infos

    @classmethod
    def _extract_file_info_binary(cls, handle):
        """Extract file info from a Maya binary file. This method will read
        the file and extract the file info from the FINF chunks.
        """
        file_infos = []
        start_offset = cls._find_file_info_start_offset(handle)
        assert start_offset != -1
        handle.seek(start_offset)
        while cls._peek(handle, 4) == cls.BINARY_FILE_INFO:
            file_infos.append(cls._parse_file_info(handle))
        return file_infos

    @staticmethod
    def _peek(handle, size):
        """Return the next "size" bytes from the file handle without"""
        with _restore_handle_position(handle):
            return handle.read(size)

    @staticmethod
    def _parse_file_info(handle):
        """Parse the file info from the given file handle. This method will
        read the file info from the handle and return a FileInfo object."""
        assert handle.read(4) == b"FINF"
        # 4-byte padding
        handle.read(4)
        # 64bit unsigned integer for size
        size = int.from_bytes(handle.read(8), byteorder="big", signed=False)
        # Calculate how many pad bytes we need as the size could be
        # anything, it needs to be packed into 8 byte chunks for 64bit Maya
        # binary files
        pad_bytes = (8 - (size % 8)) % 8
        file_info = FileInfo.from_file_handle(handle, size)
        handle.read(pad_bytes)
        return file_info

    @staticmethod
    def _find_file_info_start_offset(handle):
        """Find the offset of the first file info chunk in the given file
        handle. This method will read the file handle and return the offset
        of the first file info chunk. If no file info chunk is found, -1
        will be returned."""
        with _restore_handle_position(handle):
            handle.seek(0)
            bytes = handle.read(4)
            while bytes:
                if bytes == b"FINF":
                    offset = handle.tell() - 4
                    return offset
                bytes = handle.read(4)
        return -1


def _printable_value(value):
    """Returns a siccint version of a string with an undetermined length"""
    if len(value) > 80:
        return value[:80] + "..."
    return value


class FileInfo(object):
    """This class represents a file info object from a Maya file. This
    class provides a set of methods to create file info objects from Maya
    binary and ASCII files. The file info object contains a label and a
    value. The label is a string and the value is a string or a JSON
    object. The value can be converted to a JSON object using the value_as_json"""

    def __init__(self, label, value):
        super().__init__()
        self._label = label
        self._value = value
        self._printable_value = _printable_value(value)

    def __repr__(self):
        return "<File Info>: Label: {}, Value: {}".format(
            self._label, self._printable_value
        )

    @classmethod
    def from_ascii(cls, line):
        """Create a file info object from the given ASCII line. This method
        will parse the file info from the given line and return a FileInfo
        object."""
        line = line[:-1]
        tokenized = re.findall('(?:".*?"|\S)+', line)
        unpacked = [token[1:-1] for token in tokenized[1:]]
        inst = cls(unpacked[0], unpacked[1])
        log = get_logger(LOGGER_NAME)
        log.trace(">> %s" % inst)
        return inst

    @classmethod
    def from_file_handle(cls, handle, size):
        """Create a file info object from the given file handle. This method
        will read the file info from the given handle and return a FileInfo
        object."""
        data = handle.read(size)
        unpacked = [bytes(b).decode("ascii") for b in data.split(b"\x00") if b]
        inst = cls(unpacked[0], unpacked[1])
        log = get_logger(LOGGER_NAME)
        log.trace(">> %s" % inst)
        return inst

    @property
    def label(self):
        return self._label

    @property
    def value(self):
        return self._value

    def value_as_json(self):
        """Return the value as a JSON object. This method will convert the
        value to a JSON object and return it. If the value is not a valid
        JSON object, a ValueError will be raised."""
        value = self._value.replace('\\"', '"')
        return json.loads(value)
