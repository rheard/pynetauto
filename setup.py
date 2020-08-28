__author__ = ()
__version__ = "0.0.1"

from setuptools import setup


setup(name='pynetauto',
      version=__version__,
      description="A light Pythonic wrapper around .NET's Automation libraries.",
      url='TBD',
      packages=['netauto'],
      install_requires=['expanded-pythonnet'])
