Offline install for Deepgreen and Transducer
============================================

Run download.sh to download all the necessary binaries.
From OS distribution (repo/CD/DVD), install necessary tools.  
Note that pip is port of EPEL repo, so you may need enable 
that repo.
```
rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-relase-latest-7.noarch.rpm
```

We recomend the following

```
yum install -y epel-release
yum install -y unzip which tar more git vim sudo util-linux-ng passwd openssh-clients openssh-server
yum install -y net-tools iproute tmux

yum install -y python-devel python-pip 
pip install --upgrade pip 
pip install setuptools
``` 

Install deepgreen using downloaded binary. 
Install go 
```
sudo tar -C /usr/local -xzf go*.tar.gz
```

Also, create ~/go dir
```
mkdir ~/go
export GOPATH=~/go
```

Install python protobuf
```
sudo pip install --no-index --find-links=file:/path_to_curr_dir protobuf
```

After this, initdb and start deepgreen, then you should be able to run the basic.sql and basicpy.sql in transducer.

