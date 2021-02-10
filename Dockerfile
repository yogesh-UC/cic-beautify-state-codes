From python:3.7

#COPY ./requirement.txt/ pythonProject/requirement.txt
COPY . /pythonProject


WORKDIR /pythonProject

RUN pip3 install -r requirement.txt