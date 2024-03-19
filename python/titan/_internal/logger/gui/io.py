import json
from typing import Sequence
import zlib

from .record import TitanLogRecord


def write_records(log_records: Sequence[TitanLogRecord], filename: str):
    """Write log records to a file.

    Args:
        log_records: The log records to write
        filename: The name of the file to write the records to
    """
    write_records = [record.as_dict() for record in log_records]
    bytes_ = json.dumps(write_records).encode("ascii")
    with open(filename, "wb") as handle:
        handle.write(zlib.compress(bytes_))


def read_records(filename: str) -> Sequence[TitanLogRecord]:
    """Read log records from a file.

    Args:
        filename: The name of the file to read the records from

    Returns:
        The log records read from the file
    """
    with open(filename, "rb") as handle:
        bytes_ = zlib.decompress(handle.read())
    return [
        TitanLogRecord.from_dict(record)
        for record in json.loads(bytes_.decode("ascii"))
    ]
