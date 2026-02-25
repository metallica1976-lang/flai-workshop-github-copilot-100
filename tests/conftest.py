import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

# Snapshot of the original activities state taken at import time
_ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture
def client():
    # Arrange: restore in-memory state to the original snapshot before each test
    app_module.activities = copy.deepcopy(_ORIGINAL_ACTIVITIES)
    yield TestClient(app)
