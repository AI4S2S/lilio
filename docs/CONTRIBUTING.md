# Contributing guidelines

We welcome any kind of contribution to our software, from simple comment or question to a full fledged pull request. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). For developer information, go [here](README.dev.md)

A contribution can be one of the following cases:

1. you have a question;
1. you think you may have found a bug (including unexpected behavior);
1. you want to make some kind of change to the code base (e.g. to fix a bug, to add a new feature, to update documentation);
1. you want to make a new release of the code base.

The sections below outline the steps in each case.

## You have a question

1. use the search functionality [here](https://github.com/AI4S2S/ai4s2s/issues) to see if someone already filed the same issue;
2. if your issue search did not yield any relevant results, make a new issue;
3. apply the "Question" label; apply other labels when relevant.

## You think you may have found a bug

1. use the search functionality [here](https://github.com/AI4S2S/ai4s2s/issues) to see if someone already filed the same issue;
1. if your issue search did not yield any relevant results, make a new issue, making sure to provide enough information to the rest of the community to understand the cause and context of the problem. Depending on the issue, you may want to include:
    - the SHA hashcode of the commit that is causing your problem;
    - some identifying information (name and version number) for dependencies you're using;
    - information about the operating system;
1. apply relevant labels to the newly created issue.

## You want to make some kind of change to the code base

1. (**important**) announce your plan to the rest of the community *before you start working*. This announcement should be in the form of a (new) issue;
1. (**important**) wait until some kind of consensus is reached about your idea being a good idea;
1. if needed, fork the repository to your own Github profile and create your own feature branch off of the latest master commit. While working on your feature branch, make sure to stay up to date with the master branch by pulling in changes, possibly from the 'upstream' repository;
1. make sure the existing tests still work by running ``pytest``;
1. add your own tests (if necessary);
1. update or expand the documentation;
1. update the `CHANGELOG.md` file with change;
1. push your feature branch to (your fork of) the s2s repository on GitHub;
1. create the pull request.

In case you feel like you've made a valuable contribution, but you don't know how to write or run tests for it, or how to generate the documentation: don't let this discourage you from making the pull request; we can help you! Just go ahead and submit the pull request, but keep in mind that you might be asked to append additional commits to your pull request.

## You want to make a release

This section is for maintainers of the package.

1. Checkout ``HEAD`` of ``main`` branch with ``git checkout main`` and ``git pull``.
2. Determine what new version (major, minor or patch) to use. Package uses `semantic versioning <https://semver.org>`.
3. Bumping the version across all files is done with [bumpversion](https://github.com/c4urself/bump2version), e.g.

    ```shell
    bumpversion major
    bumpversion minor
    bumpversion patch
    ```

4. Update CHANGELOG.md with changes between current and new version and verify that the information in `CITATION.cff` is correct.
5. Run the unit tests with `hatch run test`.
6. Commit & push changes to GitHub.
7. Wait for [GitHub
    actions](https://github.com/AI4S2S/lilio/actions?query=branch%3Amain+)
    to be completed and green.

8. Create a [GitHub release](https://github.com/AI4S2S/lilio/releases/new)

    - Use version as title and tag version.
    - As description use intro text from README.md (to give context to
        Zenodo record) and changes from CHANGELOG.md

    This will:

    - trigger Zenodo into making a snapshot of your repository and sticking a DOI on it.
    - start a GitHub action that builds and uploads the new version to [PyPI](https://pypi.org/project/lilio/).
        - Which should trigger [conda-forge](https://anaconda.org/conda-forge/lilio) to update the package as well.

10. Verify

    After making the release, you should check that:

    1. The [Zenodo page](https://doi.org/10.5281/zenodo.7620212) is updated
    1. The [publishing action](https://github.com/AI4S2S/lilio/actions/workflows/python-publish.yml) ran successfully, and that `pip install lilio` installs the new version.
    1. The [conda-forge package](https://anaconda.org/conda-forge/lilio) is updated, and can be installed using conda.

11. Celebrate