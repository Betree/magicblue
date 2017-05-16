# Developing

- Pull the repo
- (optional) Create a virtual env and activate it
```
virtualenv ./venv
source ./venv/bin/activate
```
- Install bluepy `pip install bluepy webcolors`
- Run magicblueshell with `sudo ./venv/bin/python magicblue/magicblueshell.py`

# Important

- Make your pull requests against **staging** branch.

# Optional but nice

- Comment the issue or open a new one to let people know you're working on it
- I try to follow [PEP8](https://www.python.org/dev/peps/pep-0008/) conventions but that's not a requirement for contributing.

You can check your code by installing tox with `pip install tox` then running `tox` in magicblue root folder.
