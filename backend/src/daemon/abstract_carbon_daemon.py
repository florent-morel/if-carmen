from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from backend.src.common.constants import (
    CARMEN_LOGO,
)
from backend.src.common.known_exception import KnownException
from backend.src.core.registrar import register_models
from backend.src.core.yaml_config_loader import DaemonConfig, config
from backend.src.daemon.abstract_carbon_daemon import (
    CarbonDaemonResult,
)
from backend.src.daemon.carbon_daemon_result import (
    ResourceDaemonResult,
)
from backend.src.daemon.readers.reader_factory import (
    DefaultReaderFactory,
    ReaderFactory,
)
from backend.src.daemon.writers.writer_factory import (
    DefaultWriterFactory,
    WriterFactory,
)
from backend.src.schemas.resource import Resource, ResourceType

logger = logging.getLogger(__name__)

# TODO: To be removed
class AbstractCarbonDaemon(ABC):
    def __init__(
        self,
        daemon_config: DaemonConfig,
        reader_factory: ReaderFactory | None = None,
        writer_factory: WriterFactory | None = None,
    ):
        """
        Initialize the carbon daemon.

        Args:
            daemon_config: Configuration for daemon operations
            reader_factory: Factory for creating reader instances (optional)
            writer_factory: Factory for creating writer instances (optional)
        """


#         self.config: DaemonConfig = daemon_config
#         self.reader_factory: ReaderFactory = reader_factory or DefaultReaderFactory()
#         self.writer_factory: WriterFactory = writer_factory or DefaultWriterFactory()
#
#         register_models()
#
#         logger.info("Carbon Daemon initialized")
#
#     def run_carbon_daemon(self):
#         """
#         Execute the complete daemon workflow.
#
#         Returns:
#             CarbonDaemonResult containing execution results
#         """
#         start_time = time.time()
#         carbonDaemonResult = CarbonDaemonResult()
#
#         try:
#             logger.info("Starting Carbon Daemon execution")
#
#             # Iterate on each Resource Carbon Daemon Runner
#             # TODO: for
#             resourceDaemonResult = self.run()
#
#             carbonDaemonResult.dict_resource_daemon_result[resourceDaemonResult.resourceType, resourceDaemonResult]
#
#             # End of loop, store complete execution time
#             execution_time = time.time() - start_time
#             carbonDaemonResult.execution_time = execution_time
#
#             # Write results
#             self.write_results(carbonDaemonResult)
#
#             # Upload report file
#             # TODO:
#             #
#             total_execution_time = time.time() - start_time
#
#             logger.info(
#                 "Carbon Daemon execution completed successfully. processed %d resources in %.2f seconds",
#                 len(carbonDaemonResult.list_processed_resources),
#                 total_execution_time,
#             )
#
#             return carbonDaemonResult
#
#         except KnownException as e:
#             execution_time = time.time() - start_time
#             error_msg = f"known error during daemon execution: {e.formatted_string}"
#             logger.error(error_msg)
#
#             return CarbonDaemonResult(
#                 success=False, execution_time=execution_time, error_message=error_msg
#             )
#
#         except Exception as e:
#             execution_time = time.time() - start_time
#             error_msg = f"unexpected error during daemon execution: {str(e)}"
#             logger.exception(error_msg)
#
#             return CarbonDaemonResult(
#                 success=False, execution_time=execution_time, error_message=error_msg
#             )
