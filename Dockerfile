FROM node:6
MAINTAINER Kitware, Inc. <kitware@kitware.com>

EXPOSE 8080

RUN apt-get -qqy update && apt-get install -qy software-properties-common python3-software-properties && \
  apt-get update -qqy && apt-get install -qy \
    build-essential \
    git \
    libffi-dev \
    libsasl2-dev \
    libssl-dev \
    libldap2-dev \
    libpython3-dev && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

RUN npm config set progress false
RUN wget https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py

ENV CMAKE_SHORT_VERSION=3.4 CMAKE_VERSION=3.4.3 MONGO_VERSION=3.2.13

RUN curl -L "http://cmake.org/files/v${CMAKE_SHORT_VERSION}/cmake-${CMAKE_VERSION}-Linux-x86_64.tar.gz" | \
  gunzip -c | \
  tar -x -C /usr --strip-components 1
RUN curl -L "https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-${MONGO_VERSION}.tgz" | \
  gunzip -c | \
  tar -x -C /usr --strip-components 1
RUN python3 -m pip install coverage flake8 flake8-blind-except flake8-docstrings \
  httmock mock moto[server] Sphinx sphinx_rtd_theme virtualenv

RUN git clone https://github.com/xarthisius/girder /girder

WORKDIR /girder
RUN python3 -m pip install -e .[plugins,sftp]
RUN girder-install web --all-plugins --dev
