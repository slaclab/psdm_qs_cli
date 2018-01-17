from setuptools import setup

setup(name='psdm_qs_cli',
      version='0.1',
      description='Python client for interacting with the PCDS questionnaire.',
      url='https://github.com/slaclab/psdm_qs_cli.git',
      author='Murali Shankar',
      author_email='mshankar@slac.stanford.edu',
      license='MIT',
      packages=['psdm_qs_cli'],
      scripts=['psdm_qs_cli/QSGenerateExcelSpreadSheet.py', 'psdm_qs_cli/QSGenerateJSON.py',],
      zip_safe=False)
