import versioneer
from setuptools import setup

setup(name='psdm_qs_cli',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Python client for interacting with the PCDS questionnaire.',
      url='https://github.com/slaclab/psdm_qs_cli.git',
      author='Murali Shankar',
      author_email='mshankar@slac.stanford.edu',
      license='MIT',
      packages=['psdm_qs_cli'],
      scripts=['psdm_qs_cli/QSGenerateExcelSpreadSheet.py', 'psdm_qs_cli/QSGenerateJSON.py',],
      zip_safe=False)
