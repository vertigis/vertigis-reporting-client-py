## Setting up environment

All commands below are run from within the root of this folder. If using VS Code you may want to check out the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python).

### Create the virtual environment folder:

```sh
$ python3 -m venv .venv
```

### Activate the virtual environment

```sh
$ source .venv/bin/activate
```

### Check python binaries are the correct path

```sh
# Should show you the the binary from the `.venv` folder
(venv) $ which pip
(venv) $ which python
```

### Deactivate the virtual environment

```sh
(venv) $ deactivate
```

## Installing dependencies

To install both the runtime and development dependencies:

```sh
(venv) $ pip install -e ".[dev]"
```

## Submiting a pull request

The version in [`setup.py`](setup.py) will need to be updated prior to merging the PR into `master`.

## Releasing

The package will automatically be released to [PyPI](https://pypi.org/project/geocortex-reporting-client/) when a [GitHub release](https://github.com/geocortex/geocortex-reporting-client-py/releases) is created. The version of the package follows [Semantic Versioning](https://semver.org/) and is set in the [`setup.py`](setup.py) file
