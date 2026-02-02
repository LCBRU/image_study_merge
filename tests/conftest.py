import pytest
from faker import Faker
from lbrc_flask.pytest.fixtures import *
from lbrc_flask.pytest.faker import LbrcFlaskFakerProvider
from image_study_merge import create_app
from image_study_merge.config import TestConfig
from tests.faker import ImageStudyMergeProvider


@pytest.fixture(scope="function")
def app(tmp_path):
    class LocalTestConfig(TestConfig):
        FILE_UPLOAD_DIRECTORY = tmp_path

    yield create_app(LocalTestConfig)


@pytest.fixture(scope="function")
def faker():
    result: Faker = Faker("en_GB")
    result.add_provider(LbrcFlaskFakerProvider)
    result.add_provider(ImageStudyMergeProvider)

    yield result
