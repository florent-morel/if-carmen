"""
This file is used to configure pytest.
"""

import os
from pathlib import Path


os.environ["TEST_ENV"] = "True"
os.environ["EXECUTION_DATE"] = "2025-06-01"

current_file = Path(__file__)
project_root = (
    current_file.parent.parent.parent
)  # backend/tests/conftest.py -> carbon-engine/
config_path = project_root / "config-test.yaml"
os.environ["CARMEN_CONFIG_FILEPATH"] = str(config_path)

def pytest_configure():
    """
    Configure pytest environment variables.
    """
    # Environment variables are already set at module level
    pass
