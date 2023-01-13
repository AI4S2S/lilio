# lilio: Calendar generator for machine learning with timeseries data

<img align="right" width="160" alt="Logo" src="https://raw.githubusercontent.com/AI4S2S/lilio/main/docs/assets/images/ai4s2s_logo.png">


[![github repo badge](https://img.shields.io/badge/github-repo-000.svg?logo=github&labelColor=gray&color=blue)](https://github.com/AI4S2S/lilio)
[![github license badge](https://img.shields.io/github/license/AI4S2S/lilio)](https://github.com/AI4S2S/lilio)
[![fair-software badge](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-yellow)](https://fair-software.eu)
<!--
[![Documentation Status](https://readthedocs.org/projects/ai4s2s/badge/?version=latest)](https://ai4s2s.readthedocs.io/en/latest/?badge=latest)
[![build](https://github.com/AI4S2S/lilio/actions/workflows/build.yml/badge.svg)](https://github.com/AI4S2S/lilio/actions/workflows/build.yml)
[![sonarcloud](https://github.com/AI4S2S/lilio/actions/workflows/sonarcloud.yml/badge.svg)](https://github.com/AI4S2S/lilio/actions/workflows/sonarcloud.yml)
[![workflow scc badge](https://sonarcloud.io/api/project_badges/measure?project=AI4S2S_ai4s2s&metric=coverage)](https://sonarcloud.io/dashboard?id=AI4S2S_ai4s2s)
-->

A python package for generating calendars to resample timeseries into training and target data for machine learning. Named after [the inventor](https://en.wikipedia.org/wiki/Aloysius_Lilius) of the [Gregorian Calendar](https://en.wikipedia.org/wiki/Gregorian_calendar).

## Installation
[![workflow pypi badge](https://img.shields.io/pypi/v/lilio.svg?colorB=blue)](https://pypi.python.org/project/lilio/)
[![supported python versions](https://img.shields.io/pypi/pyversions/lilio)](https://pypi.python.org/project/lilio/)

To install the latest release of lilio, do:
```console
python3 -m pip install lilio
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
python3 -m pip install -e .
```

Then, run tests:
```py
python3 -m pytest
```

## How the lilio calendars work
In a typical ML-based timeseries analysis, the first step is always data processing.  A calendar-based datetime module `time` is implemented for time operations. For instance, a user is looking for predictors for winter climate at seasonal timescales (~180 days). First, a `calendar` object is created using `AdventCalendar`:

```py
>>> calendar = lilio.time.AdventCalendar(anchor="11-30", freq='180d')
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
>>> bins = lilio.time.resample(calendar, input_data)
>>> bins
  anchor_year  i_interval                  interval  mean_data  target
0        2020          -1  [2020-06-03, 2020-11-30)      275.5    True
1        2020           1  [2020-11-30, 2021-05-29)       95.5   False
2        2021          -1  [2021-06-03, 2021-11-30)      640.5    True
3        2021           1  [2021-11-30, 2022-05-29)      460.5   False
```

Depending on data preparations, we can choose different types of calendars e.g. [`MonthlyCalendar`](https://ai4s2s.readthedocs.io/en/latest/autoapi/lilio/time/index.html#lilio.time.MonthlyCalendar) and [`WeeklyCalendar`](https://ai4s2s.readthedocs.io/en/latest/autoapi/lilio/time/index.html#lilio.time.WeeklyCalendar).

<!---
## Tutorials
`lilio` supports operations that are common in a machine learning pipeline of sub-seasonal to seasonal forecasting research. Tutorials covering supported methods and functionalities are listed in [notebooks](https://github.com/AI4S2S/lilio/tree/main/notebooks). To check these notebooks, users need to install [`Jupyter lab`](https://jupyter.org/). More details about each method can be found in this [API reference documentation](https://ai4s2s.readthedocs.io/en/latest/autoapi/index.html).

## Documentation
[![Documentation Status](https://readthedocs.org/projects/ai4s2s/badge/?version=latest)](https://ai4s2s.readthedocs.io/en/latest/?badge=latest)

For detailed information on using `s2spy` package, visit the [documentation page](https://ai4s2s.readthedocs.io/en/latest/) hosted at Readthedocs.
-->

## Contributing

If you want to contribute to the development of lilio,
have a look at the [contribution guidelines](docs/CONTRIBUTING.md).

<!--
## How to cite us
[![RSD](https://img.shields.io/badge/rsd-s2spy-00a3e3.svg)](https://research-software-directory.org/software/s2spy)
<!-- [![DOI](https://zenodo.org/badge/DOI/<replace-with-created-DOI>.svg)](https://doi.org/<replace-with-created-DOI>)

TODO: add links to zenodo and rsd.
More information will follow soon.

-->

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [NLeSC/python-template](https://github.com/NLeSC/python-template).
