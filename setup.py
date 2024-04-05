from setuptools import (
    find_packages,
    setup,
)


setup(
    name='pyhtsl',
    author='Jesse Janssen',
    url='https://github.com/69Jesse/PyHTSL',
    version='0.1',
    packages=find_packages(),
    description='Python wrapper for HTSL https://github.com/BusterBrown1218/HTSL',
    python_requires='>=3.9',
    include_package_data=True,
)
