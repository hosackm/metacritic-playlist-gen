from metafy import version
from setuptools import setup, find_packages

setup(
    name="metafy",
    version=version,
    packages=find_packages(),
    install_requires=[
        "Click",
        "requests",
        "boto3",
        "scrapy",
        "python-Levenshtein",
        "fuzzywuzzy",
        "pytest-runner"
    ],
    tests_require=[
        "pytest",
        "requests_mock",
        "bs4"
    ],
    entry_points="""
        [console_scripts]
        metafy=metafy.__main__:cli
    """
)
