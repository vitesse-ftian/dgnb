Deepgreen Notebooks
====================

Installation
-------------

First, please follow the instructions in the install dir to install deepgreen.
Next, install [jupyter](http://jupyter.org/install) or [jupyterlab](https://github.com/jupyterlab/jupyterlab#installation)

Jupyter or jupyterlab can be installed on deepgreen master node or on 
client desktop.  If installed on client desktop, make sure you configure
deepgreen to allow remote sql access.  Some notebooks, esp those admin 
related, may require database super user role.

The Jupyter should install the following modules,
```
# For some plotting example, install on system.
sudo pip3 install matplotlib
# Install dg python tools, for individual user.
(cp py; python3 setup.py install --user)
```
