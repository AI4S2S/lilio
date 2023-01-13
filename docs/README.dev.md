# `lilio` developer documentation

If you're looking for user documentation, go [here](readme_link.rst).

## Development install

```shell
# Create a virtual environment, e.g. with
python3 -m venv env

# activate virtual environment
source env/bin/activate

# make sure to have a recent version of pip and setuptools
python3 -m pip install --upgrade pip setuptools

# (from the project root directory)
# install lilio as an editable package
python3 -m pip install --no-cache-dir --editable .
# install development dependencies
python3 -m pip install --no-cache-dir --editable .[dev]
```

Afterwards check that the install directory is present in the `PATH` environment variable.

## Running the tests

There are two ways to run tests.

The first way requires an activated virtual environment with the development tools installed:

```shell
pytest -v
```

The second is to use `tox`, which can be installed separately (e.g. with `pip install tox`), i.e. not necessarily inside the virtual environment you use for installing `lilio`, but then builds the necessary virtual environments itself by simply running:

```shell
tox
```

Testing with `tox` allows for keeping the testing environment separate from your development environment.
The development environment will typically accumulate (old) packages during development that interfere with testing; this problem is avoided by testing with `tox`.

### Test coverage

In addition to just running the tests to see if they pass, they can be used for coverage statistics, i.e. to determine how much of the package's code is actually executed during tests.
In an activated virtual environment with the development tools installed, inside the package directory, run:

```shell
coverage run
```

This runs tests and stores the result in a `.coverage` file.
To see the results on the command line, run

```shell
coverage report
```

`coverage` can also generate output in HTML and other formats; see `coverage help` for more information.

## Running linters locally

For linting we will use [prospector](https://pypi.org/project/prospector/) and to sort imports we will use
[isort](https://pycqa.github.io/isort/). Running the linters requires an activated virtual environment with the
development tools installed.

```shell
# linter
prospector

# recursively check import style for the lilio module only
isort --recursive --check-only lilio

# recursively check import style for the lilio module only and show
# any proposed changes as a diff
isort --recursive --check-only --diff lilio

# recursively fix import style for the lilio module only
isort --recursive lilio
```

To fix readability of your code style you can use [yapf](https://github.com/google/yapf).

You can enable automatic linting with `prospector` and `isort` on commit by enabling the git hook from `.githooks/pre-commit`, like so:

```shell
git config --local core.hooksPath .githooks
```

## Generating the API docs

```shell
cd docs
make html
```

The documentation will be in `docs/_build/html`

If you do not have `make` use

```shell
sphinx-build -b html docs docs/_build/html
```

To find undocumented Python objects run

```shell
cd docs
make coverage
cat _build/coverage/python.txt
```

To [test snippets](https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html) in documentation run

```shell
cd docs
make doctest
```

## Versioning

Bumping the version across all files is done with [bumpversion](https://github.com/c4urself/bump2version), e.g.

```shell
bumpversion major
bumpversion minor
bumpversion patch
```

## Making a release

This section describes how to make a release in 3 parts:

1. preparation
1. making a release on PyPI
1. making a release on GitHub

### (1/3) Preparation

1. Update the <CHANGELOG.md> (don't forget to update links at bottom of page)
2. Verify that the information in `CITATION.cff` is correct, and that `.zenodo.json` contains equivalent data
3. Make sure the [version has been updated](#versioning).
4. Run the unit tests with `pytest -v`

### (2/3) PyPI

First prepare a new directory, for example:
```shell
cd $(mktemp -d lilio.XXXXXX)
```

A fresh git clone ensures the release has the state of origin/main branch

```shell
git clone https://github.com/AI4S2S/lilio .
```

In a your terminal, with an activated environment which has [`hatch`](https://hatch.pypa.io/latest/) installed do:

```shell
pip install hatch --upgrade
hatch build
```

If the build was succesfull, publish it to [PyPI's test servers](https://test.pypi.org/). Note that your credentials are different between test.pypi.org and pypy.org.
```shell
hatch publish --repo test
```

Visit [https://test.pypi.org/project/lilio](https://test.pypi.org/project/lilio) and
verify that your package was uploaded successfully.

Now we can publish to PyPI:
```
hatch publish
```

### (3/3) GitHub

Don't forget to also make a [release on GitHub](https://github.com/AI4S2S/lilio/releases/new). If your repository uses the GitHub-Zenodo integration this will also trigger Zenodo into making a snapshot of your repository and sticking a DOI on it.
