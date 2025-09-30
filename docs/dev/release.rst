#################
Release procedure
#################

This page gives an overview of how Repertoire releases are made.
This information is only useful for maintainers.

Repertoire's releases are largely automated through GitHub Actions (see the `ci.yaml`_ workflow file for details).
When a new release is published on GitHub, the Repertoire client is `released to PyPI`_ with that version, a new Docker image is built and uploaded to GitHub, and documentation is built and pushed for the new version (see https://repertoire.lsst.io/v/index.html).

.. _`released to PyPI`: https://pypi.org/project/rubin-repertoire/
.. _`ci.yaml`: https://github.com/lsst-sqre/repertoire/blob/main/.github/workflows/ci.yaml

.. _regular-release:

Regular releases
================

Regular releases happen from the ``main`` branch after changes have been merged.
From the ``main`` branch you can release a new major version (``X.0.0``), a new minor version of the current major version (``X.Y.0``), or a new patch of the current major-minor version (``X.Y.Z``).
See :ref:`backport-release` to patch an earlier major-minor version.

Release tags are semantic version identifiers following the :pep:`440` specification.

1. Change log and documentation
-------------------------------

Change log messages for each release are accumulated using scriv_.
See :ref:`dev-change-log` in the *Developer guide* for more details.

When it comes time to make the release, there should be a collection of change log fragments in :file:`changelog.d`.
Those fragments will make up the change log for the new release.

Review those fragments to determine the version number of the next release.
Repertoire follows semver_, so follow its rules (summarized below) to pick the next version:

.. rst-class:: compact

- If there are any backward-incompatible changes, incremeent the major version number and set the other numbers to 0.
- If there are any new features, increment the minor version number and set the patch version to 0.
- Otherwise, increment the patch version number.

Then, run :command:`uv run scriv collect --version <version>`, specifying the version number you decided on.
This will delete the fragment files and collect them into :file:`CHANGELOG.md` under an entry for the new release.
Review that entry and edit it as needed (proofread, change the order to put more important things first, etc.).

scriv will put blank lines between entries from different files.
You may wish to remove those blank lines to ensure consistent formatting by various Markdown parsers.

Finally, create a PR from those changes and merge it before continuing with the release process.

2. GitHub release and tag
-------------------------

Create a release using `GitHub's Release feature <https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository>`__:

1. For the tag, enter the version number of the release in the :guilabel:`Find or create a new tag` box in the dropdown under :guilabel:`Select tag`.
   The tag must follow the :pep:`440` specification since Repertoire uses setuptools_scm_ to set version metadata based on Git tags.
   In particular, don't prefix the tag with ``v``.

   .. _setuptools_scm: https://github.com/pypa/setuptools-scm

2. Ensure the branch target is set appropriately (normally ``main``).

3. For the release title, repeat the version string.

4. Click the :guilabel:`Generate release notes` button to include the GitHub-generated summary of pull requests in the release notes.

5. In the release notes box above the generated notes, paste the contents of the :file:`CHANGELOG.md` entry for this release, without the initial heading specifying the version number and date.
   Adjust the heading depth of the subsections to use ``##`` instead of ``###`` to match the pull request summary.

The `ci.yaml`_ GitHub Actions workflow will upload the new release to PyPI, documentation to https://repertoire.lsst.io, and a Docker image to the GitHub Container Registry.

.. _backport-release:

Backport releases
=================

The regular release procedure works from the main line of development on the ``main`` Git branch.
To create a release that patches an earlier major or minor version, you need to release from a **release branch.**

Creating a release branch
-------------------------

Release branches are named after the major and minor components of the version string: ``X.Y``.
If the release branch doesn't already exist, check out the latest patch for that major-minor version:

.. code-block:: sh

   git checkout X.Y.Z
   git switch -c X.Y
   git push -u

Developing on a release branch
------------------------------

Once a release branch exists, it becomes the "main" branch for patches of that major-minor version.
Pull requests should be based on, and merged into, the release branch.

If the development on the release branch is a backport of commits on the ``main`` branch, use :command:`git cherry-pick` to copy those commits into a new pull request against the release branch.

Releasing from a release branch
-------------------------------

Releases from a release branch are equivalent to :ref:`regular releases <regular-release>`, except that the release branch takes the role of the ``main`` branch.
