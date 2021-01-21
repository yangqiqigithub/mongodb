#!/bin/bash
cd `dirname $0`
path=$(pwd)"/"

tar -zxvf pymongo-3.2.2.tar.gz

cd ${path}"pymongo-3.2.2"
python setup.py install


tar -zxvf pyasn1-0.4.4.tar.gz
cd ${path}"pyasn1-0.4.4" 
python setup.py install