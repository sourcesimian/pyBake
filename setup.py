from setuptools import setup


description = "Create single file standalone Python scripts with builtin frozen file system"

setup(
    name="pyBake",
    version="0.0.2",
    description=description,
    long_description=description,  # TODO: https://docs.python.org/2/distutils/packageindex.html#pypi-package-display
    author="Source Simian",
    author_email="sourcesimian@users.noreply.github.com",
    url='https://github.com/sourcesimian/pyBake',
    license='MIT',
    packages=['pybake'],
)
