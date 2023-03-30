FROM python:3.9-slim
WORKDIR /
RUN apt-get update \
    && apt-get install -y build-essential patchelf \
    && pip install pyinstaller staticx 

COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt