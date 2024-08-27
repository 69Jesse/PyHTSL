from setuptools import (
    find_packages,
    setup,
)


setup(
    name='pyhtsl',
    author='Jesse Janssen',
    url='https://github.com/69Jesse/PyHTSL',
    version='1.7.6',
    packages=find_packages() + ['pyhtsl.misc'],
    description='Python wrapper for HTSL created to simplify the process of making housings on Hypixel',
    python_requires='>=3.12',
    package_data={'': ['*.*']},
    include_package_data=True,
)
