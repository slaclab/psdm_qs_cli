import versioneer
from setuptools import setup

with open('requirements.txt', 'rt') as f:
    requirements = f.read().splitlines()

setup(
    name="psdm_qs_cli",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Python client for interacting with the PCDS questionnaire.",
    url="https://github.com/slaclab/psdm_qs_cli.git",
    author="Murali Shankar",
    author_email="mshankar@slac.stanford.edu",
    license="MIT",
    packages=["psdm_qs_cli"],
    entry_points={
        "console_scripts": [
            "QSGenerateExcelSpreadSheet.py=psdm_qs_cli.QSGenerateExcelSpreadSheet:main",
            "QSGenerateJSON.py=psdm_qs_cli.QSGenerateJSON:main",
        ],
    },
    install_requires=requirements,
    zip_safe=False,
)
