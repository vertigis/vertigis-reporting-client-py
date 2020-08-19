## Setting up environment

All commands are run from within the root of this folder.

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
# Should show you the the binary from the venv folder
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
