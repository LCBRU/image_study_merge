import os
from lbrc_flask.config import BaseConfig, BaseTestConfig


class Config(BaseConfig):
    FILE_UPLOAD_DIRECTORY = os.environ["FILE_UPLOAD_DIRECTORY"]


class TestConfig(BaseTestConfig):
    pass
