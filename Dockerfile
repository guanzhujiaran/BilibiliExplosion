FROM cimg/python:3.13.7-browsers

LABEL authors="1944637830@qq.com"

WORKDIR /fastapi_app/

COPY . .

RUN pip install -r requests.txt

