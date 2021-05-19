FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
RUN pip install /app
RUN rm -r ./oscp

RUN useradd -s /bin/bash admin
RUN mkdir /data
RUN chown -R admin /app && chown -R admin /data

USER admin
VOLUME /data
ENV TZ="Europe/Berlin"
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:9000 --chdir=./ --worker-tmp-dir /dev/shm --workers=2 --threads=4 --worker-class=gthread"
EXPOSE 9000

CMD ["gunicorn", "start:app"] #.py"]
