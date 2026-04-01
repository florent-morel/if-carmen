"""
Compute reader module for reading virtual machine data from various sources.
"""

from backend.src.daemon.readers.compute.reader_compute_azure import (
    AzureComputeReaderStrategy,
)
from backend.src.daemon.readers.compute.reader_compute_local import (
    LocalComputeReaderStrategy,
)

from backend.src.daemon.readers.abstract_reader import Reader

__all__ = [
    "Reader",
    "ReaderComputeAzure",
    "ReaderComputeLocal",
]
