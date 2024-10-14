# Instructions for development

## Dependency management and dev environment
Poetry is used as a backend for packaging and for dependency
management. To set up a working development environment, create
a virtual environment and install the `poetry` python package.
Then `poetry install` installs all develpoment dependencies:

```bash
python3.11 -m venv <name_of_venv>
source <name_of_venv>/bin/activate
pip install poetry
poetry install
```

## Testing
The tests are maintained in the subpackages under `tests`, e.g.
`menu_tools/object_performance/tests`. After properly setting up
a development environment as described [above](#dependency-management-and-dev-environment)
you can simply run

```bash
pytest -vv
```

to run all tests. The `-vv` option is optional and can be omitted.
For some of the tests the presence of the `V29` caching files is required.


## Code Formatting and Linting
`black` is used for code formatting and `flake8` for linting.
These tools are helpful to have consistent formatting through
the codebase even with multiple developers working on the code.
To run `black`, set up the development environment as described
[above](#dependency-management-and-dev-environment) and run

```bash
black menu_tools
```

If you want to dry-run, add the `--check` flag to see which files would
be modified.
Similarlly `flake8` can be run by simply typing

```bash
flake8 menu_tools
```
