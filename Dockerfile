FROM python:3.8

WORKDIR /opt/turtle_test

ADD requirements.txt /opt/turtle_test/
RUN pip install -r requirements.txt
