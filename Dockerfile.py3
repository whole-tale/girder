FROM node:6-stretch
MAINTAINER Kitware, Inc. <kitware@kitware.com>

EXPOSE 8080

RUN mkdir /girder
RUN mkdir /girder/logs

RUN apt-get -qqy update && apt-get install -qy software-properties-common python3-software-properties && \
  apt-get update -qqy && apt-get install -qy \
    build-essential \
    git \
    xsltproc \
    python3-cairo \
    python3-gi \
    python3-gi-cairo \
    libffi-dev \
    libsasl2-dev \
    libssl-dev \
    libldap2-dev \
    libpango1.0-dev \
    libpython3-dev && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

RUN wget -q https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py

WORKDIR /girder
COPY girder /girder/girder
COPY clients /girder/clients
COPY plugins /girder/plugins
COPY scripts /girder/scripts
COPY grunt_tasks /girder/grunt_tasks
COPY Gruntfile.js /girder/Gruntfile.js
COPY setup.py /girder/setup.py
COPY package.json /girder/package.json
COPY README.rst /girder/README.rst

RUN python3 -m pip install --no-cache-dir -q \
  -r plugins/wholetale/requirements.txt \
  -e .[plugins,sftp]
ENV NPM_CONFIG_LOGLEVEL=warn NPM_CONFIG_COLOR=false NPM_CONFIG_PROGRESS=false
RUN girder-install web --all-plugins && \
  rm -rf /root/.npm /tmp/npm* /girder/node_modules

#RUN python3 -c "import nltk; nltk.download('wordnet')"
#RUN python3 -m spacy download en

COPY girder.local.cfg.dev /girder/girder/conf/girder.local.cfg

ENTRYPOINT ["python3", "-m", "girder"]
