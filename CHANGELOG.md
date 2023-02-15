# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## 0.3.1 (2023-02-15)

### Changed
- `lilio.resample` will now return `xr.DataArray` if the input is `xr.DataArray`.
- For compatibility with DataArray output, the Dataset/DataArray returned by resample now has the coordinates "left_bound" and "right_bound" instead of a single "intervals" coordinate with the "bounds" dimension.
- If your input data has an frequency of less than _twice_ the Calendar's smallest interval length, a UserWarning will be raised.
- If your input data has a frequency less than the Calendar's smallest interval length, a ValueError will be raised.
- In the output of `resample()`, the column/coordinate `target` has been renamed to `is_target` to avoid clashing with a possibly commonly used name by users.
- The input data into `resample()` is now checked for the existance of reserved names, such as "anchor_year" or "i_interval", to avoid overwriting these and cause unpredictable behavior.

## 0.3.0 (2023-02-08)

First release of Lilio as a split off from `s2spy`.

Lilio generates calendars to resample timeseries into training and target data for machine learning.
It is named after [the inventor](https://en.wikipedia.org/wiki/Aloysius_Lilius) of the [Gregorian Calendar](https://en.wikipedia.org/wiki/Gregorian_calendar).

### Fixed
- Fixed a bug in Matplotlib calendar visualization related to the anchor date.

### Changed
- The `CustomCalendar` has been renamed to `Calendar`.
- The `AdventCalendar`, `MonthlyCalendar` and `WeeklyCalendar` have been removed as classes. Instead there are functions that generate a standard `Calendar`.

### Added
- Resampling now supports many methods (e.g. median, min, std) as well as user-defined functions.
- A "calendar shifter" to create a list of staggered calendars.

### Dev changes
- Lilio makes use of ['hatch'](https://hatch.pypa.io/) now.
  - Building the package has moved to hatchling
  - Environments and scripts are set up to handle linting and docs building.
- Ruff is now used as a linter.
- Notebooks have been moved to the docs folder. Notebooks needs to be cleaned to pass the CI.

## 0.2.1 (2022-09-02)

### Fixed
- Display of images on ReadtheDocs and PyPi ([#97](https://github.com/AI4S2S/s2spy/pull/97))

## 0.2.0 (2022-09-01)

### Added
- Improve Sphinx documentation hosted on ReadtheDocs ([#32](https://github.com/AI4S2S/s2spy/pull/32) [#70](https://github.com/AI4S2S/s2spy/pull/70))
- Support max lags and mark target period methods in time module ([#40](https://github.com/AI4S2S/s2spy/pull/40) [#43](https://github.com/AI4S2S/s2spy/pull/43))
- Add traintest splitting module for cross-validation ([#37](https://github.com/AI4S2S/s2spy/pull/37))
  - Support sklearn splitters for traintest module ([#53](https://github.com/AI4S2S/s2spy/pull/53))
  - Implement train/test splits iterator ([#70](https://github.com/AI4S2S/s2spy/pull/70))
- Add Response Guided Dimensionality Reduction (RGDR) module ([#68](https://github.com/AI4S2S/s2spy/pull/68))
  - Implement correlation map function ([#49](https://github.com/AI4S2S/s2spy/pull/49))
  - Implement dbscan for RGDR ([#57](https://github.com/AI4S2S/s2spy/pull/57))
  - Support for multiple lags in RGDR ([#85](https://github.com/AI4S2S/s2spy/pull/85))
- Update Readme ([#95](https://github.com/AI4S2S/s2spy/pull/95))

### Changed
- Refactor resample methods as functions ([#50](https://github.com/AI4S2S/s2spy/issues/50))
- Refactor calendars to BaseCalendar class and subclasses ([#60](https://github.com/AI4S2S/s2spy/pull/60))

### Removed
- Python 3.7 support ([#65](https://github.com/AI4S2S/s2spy/issues/65))

## 0.1.0 (2022-06-28)

### Added
- Time module for an "advent calendar" to handle target and precursor periods.
- Implemented resampling data to the advent calendar.
- Example notebooks on how to use the calendar and resampling functionalities.

[Unreleased]: https://github.com/AI4S2S/lilio