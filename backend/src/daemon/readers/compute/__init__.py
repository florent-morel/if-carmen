"""
Compute reader module for reading virtual machine data from various sources.
"""

from backend.src.daemon.readers.compute.azure_compute_reader import (
    AzureComputeReaderStrategy,
)
from backend.src.daemon.readers.compute.local_compute_reader import (
    LocalComputeReaderStrategy,
)

from backend.src.daemon.readers.abstract_reader import Reader

__all__ = [
    "Reader",
    "ReaderComputeAzure",
    "ReaderComputeLocal",
]
