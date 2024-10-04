# noxfile.py

# third-party packages
import nox

nox.sessions = [
    "package",
    "lint",
    "tests",
]

locations = [
    "src",
    "tests",
    "./noxfile.py",
    "examples",
]


@nox.session(python=False)
def package(session):
    session.run("poetry", "build")
    session.run("poetry", "install")


@nox.session(python=False)
def lint(session):
    args = session.posargs or locations
    session.run("poetry", "run", "flake8", *args)


@nox.session(python=False)
def tests(session):
    session.run(
        "poetry",
        "run",
        "pytest",
        "--cov",
        "gbfs_analytics",
        "--cov-report",
        "xml",
        "--cov-report",
        "term-missing",
        "--junitxml",
        "coverage.xml",
    )
