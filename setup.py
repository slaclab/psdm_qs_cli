from setuptools import setup

setup(name='psdm_qs_cli',
      version='0.1',
      description='Python client for interacting with the PCDS questionnaire',
      url='https://github.com/slaclab/psdm_qs_cli.git',
      author='Murali Shankar',
      author_email='mshankar@slac.stanford.edu',
      license='MIT',
      packages=['qs_cli'],
      scripts=['qs_cli/cool', 'qs_cli/skype',]
      zip_safe=False)
