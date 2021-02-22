From alpine:3.7

COPY ./requirements.txt/ pythonProject/requirements.txt
# COPY . /pythonProject


WORKDIR /pythonProject

RUN pip3 install -r requirements.txt