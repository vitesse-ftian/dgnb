#!/bin/bash

function download {
if [ -f $2 ]; then
    echo "Using already downloaded $2." 
else 
    echo "Download $2." 
    /usr/bin/curl -O $1/$2 
fi
}

DEEPGREEN=deepgreendb.16.23.rh6.x86_64.171121.bin
GO=go1.9.1.linux-amd64.tar.gz

download https://media.githubusercontent.com/media/vitessedata/download/master $DEEPGREEN
download https://storage.googleapis.com/golang $GO
pip download protobuf 
