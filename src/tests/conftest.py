from typing import Dict, Generator
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.core.config import settings
from src.main import app


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope='function')
def custom_tmpdir_factory():
    custom_base_temp_dir = settings.REPO_ROOT
    os.makedirs(custom_base_temp_dir, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix='pytest-', dir=custom_base_temp_dir)


@pytest.fixture(scope='function')
def custom_tmpdir(custom_tmpdir_factory):
    with custom_tmpdir_factory as temp_dir_path:
        yield temp_dir_path
