"""
Compute reader module for reading virtual machine data from various sources.
"""

from backend.src.daemon.readers.compute.reader_compute_azure import (
    ReaderComputeAzure,
)
from backend.src.daemon.readers.compute.reader_compute_local import (
    ReaderComputeLocal,
)

# from backend.src.daemon.readers.abstract_reader import AbstractReader

__all__ = [
    "Reader",
    "ReaderComputeAzure",
    "ReaderComputeLocal",
]
