## Setting up environment

All commands are run from within the root of this folder.

### Create the virtual environment folder:

```sh
$ python3 -m venv ./venv
```

### Activate the virtual environment

```sh
$ source ./venv/bin/activate
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

## Managing dependencies

### Installing packages

Within an activated environment

```sh
(venv) $ pip install numpy
(venv) $ pip list
Package    Version
---------- -------
numpy      1.17.0
pip        20.1.1
setuptools 47.1.0
```

If you open up the `venv/lib/pythonx.x/site-package` directory you can see that `numpy` is installed within this folder but not within the global namespace which is exactly what we want.

### Tracking project dependencies

In order to tell our co-workers what packages our project depends on, we would usually use a `requirements.txt` file within the root of the project folder.

To do that we can actually use the `pip freeze` command and pipe it to the requirements.txt file:

```sh
(venv) $ pip freeze > requirements.txt
```

Finally, when a co-worker receives a copy of your project source code, he will need to install the dependencies. To do that he will spin up his own virtual environment and then run:

```sh
(venv) $ pip install -r requirements.txt
```
