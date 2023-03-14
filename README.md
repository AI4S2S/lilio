# lilio: Calendar generator for machine learning with timeseries data

<img align="right" width="160" alt="Logo" src="https://raw.githubusercontent.com/AI4S2S/lilio/main/docs/assets/images/lilio_logo.png">


<!--[![github repo badge](https://img.shields.io/badge/github-repo-000.svg?logo=github&labelColor=gray&color=blue)](https://github.com/AI4S2S/lilio) -->
[![github license badge](https://img.shields.io/github/license/AI4S2S/lilio)](https://github.com/AI4S2S/lilio)
[![rsd badge](https://img.shields.io/badge/RSD-lilio-blue)](https://research-software-directory.org/software/lilio)
[![DOI](https://zenodo.org/badge/588084019.svg)](https://zenodo.org/badge/latestdoi/588084019)
[![SQAaaS badge shields.io](https://img.shields.io/badge/sqaaas%20software-gold-yellow)](https://api.eu.badgr.io/public/assertions/P3scOSLyQVWzzsjq0Ueycw "SQAaaS gold badge achieved")
[![fair-software.eu](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F-green)](https://fair-software.eu)
[![Documentation Status](https://readthedocs.org/projects/ai4s2s/badge/?version=stable)](https://lilio.readthedocs.io/en/stable/?badge=stable)
[![build](https://github.com/AI4S2S/lilio/actions/workflows/build.yml/badge.svg)](https://github.com/AI4S2S/lilio/actions/workflows/build.yml)
[![workflow scc badge](https://sonarcloud.io/api/project_badges/measure?project=AI4S2S_lilio&metric=coverage)](https://sonarcloud.io/dashboard?id=AI4S2S_lilio)
<!--[![sonarcloud](https://github.com/AI4S2S/lilio/actions/workflows/sonarcloud.yml/badge.svg)](https://github.com/AI4S2S/lilio/actions/workflows/sonarcloud.yml) -->

A python package for generating calendars to resample timeseries into training and target data for machine learning. Named after [the inventor](https://en.wikipedia.org/wiki/Aloysius_Lilius) of the [Gregorian Calendar](https://en.wikipedia.org/wiki/Gregorian_calendar).

Lilio was originally designed for use in [`s2spy`](https://github.com/AI4S2S/s2spy), a high-level python package integrating expert knowledge and artificial intelligence to boost (sub) seasonal forecasting.

## Installation
[![workflow pypi badge](https://img.shields.io/pypi/v/lilio.svg?colorB=blue)](https://pypi.python.org/project/lilio/)
[![supported python versions](https://img.shields.io/pypi/pyversions/lilio)](https://pypi.python.org/project/lilio/)
[![conda-forge](https://anaconda.org/conda-forge/lilio/badges/version.svg)](https://anaconda.org/conda-forge/lilio)

To install the latest release of lilio, do:
```console
python3 -m pip install lilio
```

Lilio is also available on conda-forge. If you use conda, do:
```console
conda install -c conda-forge lilio
```

To install the in-development version from the GitHub repository, do:

```console
python3 -m pip install git+https://github.com/AI4S2S/lilio.git
```

### Configure the package for development and testing
A more extensive developer guide can be found [here](./docs/README.dev.md).

The testing framework used here is [pytest](https://pytest.org). Before running the test, we get a local copy of the source code and install `lilio` via the command:

```py
git clone https://github.com/AI4S2S/lilio.git
cd lilio
python3 -m pip install -e .[dev]
```

Then, run tests:
```py
hatch run test
```

## How the lilio calendars work

In Lilio, calendars are 2-dimensional. Each row (year) represents a unique
observation, whereas each column corresponds to a precursor period with a
certain lag. This is how we like to structure our data for ML applications.

![Conceptual illustration of Lilio Calendar](https://raw.githubusercontent.com/AI4S2S/lilio/main/docs/assets/images/calendar_concept.png)

We define the "anchor date" to be between the target and precursor periods
(strictly speaking, it is the start of the first target interval). All other
intervals are expressed as offsets to this anchor date. Conveniently, this
eliminates any ambiguity related to leap years.

Here's a calendar generated with Lilio:

```py
>>> calendar = lilio.daily_calendar(anchor="11-30", length='180d')
>>> calendar = calendar.map_years(2020, 2021)
>>> calendar.show()
i_interval                         -1                         1
anchor_year
2021         [2021-06-03, 2021-11-30)  [2021-11-30, 2022-05-29)
2020         [2020-06-03, 2020-11-30)  [2020-11-30, 2021-05-29)
```

Now, the user can load the data `input_data` (e.g. `pandas` `DataFrame`) and resample it to the desired timescales configured in the calendar:

```py
>>> calendar = calendar.map_to_data(input_data)
>>> bins = lilio.resample(calendar, input_data)
>>> bins
  anchor_year  i_interval                  interval  mean_data  target
0        2020          -1  [2020-06-03, 2020-11-30)      275.5    True
1        2020           1  [2020-11-30, 2021-05-29)       95.5   False
2        2021          -1  [2021-06-03, 2021-11-30)      640.5    True
3        2021           1  [2021-11-30, 2022-05-29)      460.5   False
```

For convenience, Lilio offers a few shorthands for standard of calendars e.g.
[`monthly_calendar`](https://lilio.readthedocs.io/en/latest/autoapi/lilio/calendar_shorthands/index.html#lilio.calendar_shorthands.monthly_calendar)
and
[`weekly_calendar`](https://lilio.readthedocs.io/en/latest/autoapi/lilio/calendar_shorthands/index.html#lilio.calendar_shorthands.weekly_calendar).
However, you can also create custom calendars by calling
[`Calendar`](https://lilio.readthedocs.io/en/latest/autoapi/lilio/calendar/index.html#lilio.calendar.Calendar)
directly. For a nice walkthrough, see [this example
notebook](https://lilio.readthedocs.io/en/latest/notebooks/all_about_the_calendar.html).

<!---
## Tutorials
`lilio` supports operations that are common in a machine learning pipeline of sub-seasonal to seasonal forecasting research. Tutorials covering supported methods and functionalities are listed in [notebooks](https://github.com/AI4S2S/lilio/tree/main/notebooks). To check these notebooks, users need to install [`Jupyter lab`](https://jupyter.org/). More details about each method can be found in this [API reference documentation](https://ai4s2s.readthedocs.io/en/latest/autoapi/index.html).

-->
## Documentation
[![Documentation Status](https://readthedocs.org/projects/lilio/badge/?version=latest)](https://lilio.readthedocs.io/en/latest/?badge=latest)

For detailed information on using `lilio` package, visit the [documentation page](https://lilio.readthedocs.io/en/latest/) hosted at Readthedocs.

## Contributing

If you want to contribute to the development of lilio,
have a look at the [contribution guidelines](docs/CONTRIBUTING.md).

## How to cite us
[![rsd badge](https://img.shields.io/badge/RSD-lilio-blue)](https://research-software-directory.org/software/lilio)
[![DOI](https://zenodo.org/badge/588084019.svg)](https://zenodo.org/badge/latestdoi/588084019)

Please use the Zenodo DOI to cite this package if you used it in your research.

## Acknowledgements
This package was developed by the Netherlands eScience Center and Vrije Universiteit Amsterdam under Netherlands eScience Center grant NLESC.OEC.2021.005.

The package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [NLeSC/python-template](https://github.com/NLeSC/python-template).
