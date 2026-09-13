import pytest
from freegpt.config import CONFIG, DEFAULT_CONFIG

@pytest.fixture(autouse=True)
def reset_config():
    original = dict(CONFIG)
    CONFIG.clear()
    CONFIG.update(DEFAULT_CONFIG)
    yield
    CONFIG.clear()
    CONFIG.update(original)
