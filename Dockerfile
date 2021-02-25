FROM ubuntu:latest

RUN apt-get update && apt-get install -y python3

RUN apt-get install -y python3-pip

RUN apt-get install -y python3-dev libpq-dev

COPY /entrypoint.sh /

RUN ["chmod", "+x", "/entrypoint.sh"]

EXPOSE 5000


