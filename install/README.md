Install/Enable Deepgreen Data Science Tools
===========================================

First, download and install latest [deepgreen](https://vitessedata.com/deepgreen-db-download/).  Then run
```
dg setup -all dbname
```

You can run dg setup against template1 so that later created database
will automatically setup everything.   To use data science features you
need to install necessary software on all hosts in deepgreen 
cluster (use gpssh).  We recommend you to install at least golang and 
python transducer.

To Enable java transducer and xdrive to connect other database using JDBC
--------------------------------------------------------------------------
Install JDK/JRE 1.8+ 

Enable golang Transducer
------------------------
Download [golang 1.9.1](https://storage.googleapis.com/golang/go1.9.1.linux-amd64.tar.gz) 
```
sudo tar -C /usr/local -xzf go1.9.1.linux-adm64.tar.gz
mkdir ~/go
```

Enable python Transducer
------------------------
Need to install python protobuf
```
sudo pip install protobuf
```

Enable tensorflow
-----------------
Follow [tensorflow install instruction](https://www.tensorflow.org/install).  Tensorflow installation
includes python protobuf.

