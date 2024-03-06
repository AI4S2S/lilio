# `lilio` developer documentation

If you're looking for user documentation, go [here](readme_link.rst).

## Development install
For a full development enviroment run the commands below.

*Note that this is optional:* if you already have `hatch` in your main environment, this setup is not needed, as you can use the `hatch` environments to run all commands.

```shell
# Create a virtual environment, e.g. with
python3 -m venv env_name

# activate virtual environment
source env_name/bin/activate
# Or on windows:
#  env_name/Scripts/Activate.ps1

# make sure to have a recent version of pip and hatch
python3 -m pip install --upgrade pip hatch

# (from the project root directory)
# install lilio as an editable package
python3 -m pip install --no-cache-dir --editable .
# install development dependencies
python3 -m pip install --no-cache-dir --editable .[dev]
```

Afterwards check that the install directory is present in the `PATH` environment variable.

## Running the tests

Lilio uses `pytest` for unit testing. Running tests has been configured using `hatch`, and can be started by running:

```shell
hatch run test
```

In addition to just running the tests to see if they pass, they can be used for coverage statistics, i.e. to determine how much of the package's code is actually executed during tests.
Inside the package directory, run:

```shell
hatch run coverage
```

This runs tests and prints the results to the command line, as well as storing the result in a `coverage.xml` file (for analysis by, e.g. SonarCloud).

## Running linters locally

For linting and code style we use `ruff`. We additionally use `mypy` to check the type hints.
All tools can simply be run by doing:

```shell
hatch run lint
```

To comply with formatting you can run:

```shell
hatch run format
```

## Generating the documentation
To generate the documentation, simply run the following command. This will also test the documentation code snippets. Note that you might need to install [`pandoc`](https://pandoc.org/) to be able to generate the documentation.

```shell
hatch run docs:build
```

The documentation will be in `docs/_build/html`.

You can also make use of the [sphinx-autobuild](https://pypi.org/project/sphinx-autobuild/) plugin to show a live preview of the documentation, which can make developing the documentation a bit easier.

## Versioning

Bumping the version across all files is done with [bumpversion](https://github.com/c4urself/bump2version), e.g.

```shell
bumpversion major
bumpversion minor
bumpversion patch
```

## Making a release

This section describes how to make a release in 3 parts: preparation, release and validation.

### Preparation

1. Update the `CHANGELOG.md` file
2. Verify that the information in `CITATION.cff` is correct
3. Make sure the [version has been updated](#versioning).
4. Run the unit tests with `hatch run test`

### Making the GitHub release

Make a release and tag on GitHub.com. This will:

 - trigger Zenodo into making a snapshot of your repository and sticking a DOI on it.
 - start a GitHub action that builds and uploads the new version to [PyPI](https://pypi.org/project/lilio/).
    - Which should trigger [conda-forge](https://anaconda.org/conda-forge/lilio) to update the package as well.


### Validation

After making the release, you should check that:

1. The [Zenodo page](https://doi.org/10.5281/zenodo.7620212) is updated
1. The [publishing action](https://github.com/AI4S2S/lilio/actions/workflows/python-publish.yml) ran successfully, and that `pip install lilio` installs the new version.
1. The [conda-forge package](https://anaconda.org/conda-forge/lilio) is updated, and can be installed using conda.
