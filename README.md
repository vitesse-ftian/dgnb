# dgnb
Deepgreen Notebooks

First, please follow the instructions in the install dir to install deepgreen.

Then, please install jupyterlab.  You can install jupyterlab on the
same machine as deepgreen master, run jupyter lab on deepgreen masteror
and open web access to jupyter lab. Or, you can install jupyther 
on client desktop.  Make sure you update deepgreen to allow sql remote 
connection.  Some notebook, esp those admin related, may require database
super user role.

The Jupyter should install the following modules,
```
# For some plotting example, install on system
sudo pip3 install matplotlib

# For deepgreen tools, install for individual user.
git clone https://github.com/vitesse-ftian/dgtools
cd dgtools/py
python3 setup.py install --user
```

