FROM ubuntu:18.04

# Install Rabbit MQ -------------------------------------

RUN apt-get update && apt-get install -y wget gnupg systemd

RUN echo 'deb http://www.rabbitmq.com/debian/ testing main' | tee /etc/apt/sources.list.d/rabbitmq.list && \
	wget -O- https://www.rabbitmq.com/rabbitmq-release-signing-key.asc | apt-key add -

RUN apt-get update && \
	apt-get install -y rabbitmq-server && \
	update-rc.d rabbitmq-server defaults

# install required libraries ----------------------------

WORKDIR /deeplearning

COPY piprequirements.txt .

RUN apt-get install -y python3 python3-pip

RUN pip3 install pytest

RUN pip3 install -r piprequirements.txt

# copy sourcecode into container ------------------------

COPY dlapplication dlapplication-dev

COPY dlplatform dlplatform-dev

# create platform python package ------------------------

WORKDIR /deeplearning/dlplatform-dev

RUN python3 setup.py install

WORKDIR /deeplearning

# entrypoint: start rabbitmq-server and bash

CMD [ "/bin/bash", "-c" , "service rabbitmq-server start && /bin/bash" ]
