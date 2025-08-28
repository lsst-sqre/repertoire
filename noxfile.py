"""nox configuration for Repertoire."""

import nox
from nox_uv import session

# Default sessions.
nox.options.sessions = ["lint", "typing", "test", "docs"]

# Other nox defaults.
nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True


@session(uv_only_groups=["lint"], uv_no_install_project=True)
def lint(session: nox.Session) -> None:
    """Run pre-commit hooks."""
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@session(uv_groups=["dev"])
def test(session: nox.Session) -> None:
    """Test both the server and the client."""
    session.run("pytest", *session.posargs)


@session(uv_groups=["dev", "typing"])
def typing(session: nox.Session) -> None:
    """Run mypy."""
    session.run(
        "mypy",
        *session.posargs,
        "noxfile.py",
        "src",
        "tests",
    )
    session.run(
        "mypy",
        *session.posargs,
        "--namespace-packages",
        "--explicit-package-bases",
        "client/src",
        env={"MYPYPATH": "client/src:client"},
    )
