#FROM alpine as builder
#WORKDIR /
#RUN apk add git
#RUN git clone https://github.com/mobilityhouse/ocpp.git

FROM python:3.8-slim
#COPY requirements.txt ./
RUN pip install --no-cache-dir flask-restx gunicorn requests packaging
WORKDIR /app
COPY . /app
RUN pip install /app
RUN rm -r ./oscp

RUN useradd -s /bin/bash admin

USER admin
VOLUME /data
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:9000 --chdir=./ --worker-tmp-dir /dev/shm --workers=2 --threads=4 --worker-class=gthread"
EXPOSE 9000

CMD ["gunicorn", "start:app"] #.py"]
