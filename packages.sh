#!/bin/bash

apt-get remove python-pip
apt-get remove python3-pip
apt-get install python3-dev

easy_install3 -U pip
#pip3 install googlefinance.client
apt-get install python3-pandas
pip3 install pandas-datareader

apt-get install libfreetype6-dev
apt-get install libpng12-dev
apt-get install libatlas-base-dev
pip3 install numpy==1.14.4 --upgrade
pip3 install matplotlib --upgrade

pip3 install telegram-send
