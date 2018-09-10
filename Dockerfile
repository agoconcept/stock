FROM ubuntu:16.04

RUN apt-get update

# common tools
RUN apt-get install -y apt-utils pkg-config

# python3
RUN apt-get install -y python3-dev
RUN apt-get install -y python3-pip
RUN easy_install3 -U pip

# pandas
RUN pip3 install pandas==0.23.4 --upgrade

# alpha vantage
RUN pip3 install alpha_vantage==2.1.0 --upgrade

# matplotlib
RUN apt-get install -y libfreetype6-dev libpng12-dev libatlas-base-dev
RUN pip3 install matplotlib==2.2.2 --upgrade

# telegram-send
RUN apt-get install -y libffi-dev libssl-dev
RUN pip3 install telegram-send==0.20

# pdfunite
RUN apt-get install -y poppler-utils

# app
COPY telegrambot.py stockReport.py token.* app/
COPY telegram-send.conf /root/.config/
CMD cd /app && ./telegrambot.py

