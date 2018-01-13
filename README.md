# dgnb
Deepgreen Notebooks

First, please follow the instructions in the install dir to install deepgreen.
Then, please install jupyterlab.  We recommend install jupyterlab on the
same machine as deepgreen master, then either run jupyter notebook from deepgreen
master, or, run jupyter lab on deepgreen master and with web access.

Jupyter on deepgreen master should install the following modules
```
# For some plotting example
sudo pip3 install matplotlib

# For deepgreen tools
git clone https://github.com/vitesse-ftian/dgtools
cd dgtools/py
python3 setup.py install --user
```

