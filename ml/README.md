# Running Deepgreen with Xilinx ml-suite

# Installation
First install Xilinx ml-suite, make sure it works.
Install deepgreen V18.   Note that if you are using ubuntu, /bin/sh maybe dash.  Symlink /bin/sh 
to /bin/bash.   gpinitsystem, then create a database.

# Edit conda2.sh
Make sure CONDA2PATH and MLSUITE\_ROOT points to right dir.   The conda2.sh use Xilinx 1525, you
may need to to change it, for example to nimbix (if running on nimbix).   source this file.

# Start ml-suite backend
We ship two examples, googlnet.py which is an image classifier and yolov2.py, which is a object
detection network.  We will just use googlenet.py as exmaple.
```
rm -f /tmp/ml.socket; python googlenet.py server /tmp/ml.socket
```
You should see server starts and print some stuff to console.  You can check if it is running
by
```
python googlenet client /tmp/ml.socket
```

# Start xdrive
Make sure deepgreen v18 path is set up, (which xdrctl).   You need to edit 
the xdrive/xdrive.toml file to point to the right directory.   xdrive must
use absolute path.

```
cd xdrive
xdrctl deploy ./xdrive.toml
mkdir plugin/dgtools
cp ls_file plugin/dgtools
xdrctl start ./xdrive.toml
```

# Start database
gpstart to start database, create a database named xilinx.  Run `dg setup -all xilinx`.
Run
```
cd sql
psql -f xt.sql xilinx
psql -f gnetfun.sql xilinx
```

# Start jupyter notebook.
Start jupyter.   Try work out the googlenet notebook.  In the notebook we also have
some hard coded paths that you need to change.

The images used in example are pandas from 101 Object Categories.   It has about 9000
images.   I only checked in panda.   Classfiy all 9000 images actually does not take 
too long -- but the data is too much for github. 
