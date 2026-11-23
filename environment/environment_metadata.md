# Tested environment

Target: Windows 11 AMD64 / CPython 3.12.10. The current package version is 0.1.0.

Direct tested dependencies are NumPy 2.5.5 for ranking runtime and pytest 9.2.0 for synthetic tests. All other runtime helpers use the Python standard library. These pins are tested versions, not minimum supported versions or a full transitive lock. No cross-platform compatibility claim is made.

The fresh check pins pip 25.0.1, setuptools 80.9.0 and wheel 0.45.1 as separate setup/build tools. Exact installed packages and the executed platform are listed in `validation/clean-room/current/ENVIRONMENT_METADATA.txt`. No broad historical environment snapshot is needed or included in this candidate.
