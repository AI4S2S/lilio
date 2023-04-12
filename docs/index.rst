.. lilio documentation master file, created by
   sphinx-quickstart on Wed May  5 22:45:36 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. include:: ../README.md
   :parser: myst_parser.sphinx_

Table of contents
*****************

.. toctree::
    :maxdepth: 2

    Readme <readme_link>

.. toctree::
    :caption: Example Notebooks
    :maxdepth: 2

    notebooks/all_about_the_calendar.ipynb
    notebooks/calendar_shorthands.ipynb
    notebooks/tutorial_resampling_data.ipynb
    notebooks/tutorial_traintest.ipynb
    notebooks/tutorial_calendar_shifter.ipynb

.. toctree::
    :caption: Technical information
    :maxdepth: 2

    Scaling up Lilio with Dask <dask_integration.md>
    Developer Readme <README.dev.md>
    Contributing guide <contributing_link>
    Changelog <CHANGELOG.md>
    API reference <autoapi/index.rst>

.. toctree::
    :caption: Quick links

    Lilio on Github <https://github.com/ai4s2s/lilio>

.. toctree::
    :maxdepth: 0
    :hidden:

    Code of Conduct <CODE_OF_CONDUCT.md>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
