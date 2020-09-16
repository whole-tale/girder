FROM node:8-buster
MAINTAINER Kitware, Inc. <kitware@kitware.com>

EXPOSE 8080

RUN mkdir /girder
RUN mkdir /girder/logs

RUN apt-get -qqy update && apt-get install -qy software-properties-common python3-software-properties && \
  apt-get update -qqy && apt-get install -qy \
    build-essential \
    git \
    vim \
    gosu \
    xsltproc \
    python3-cairo \
    python3-gi \
    python3-gi-cairo \
    libcairo2 libcairo2-dev libcairo-gobject2 \
    libffi-dev \
    libfuse-dev \
    libsasl2-dev \
    libssl-dev \
    libldap2-dev \
    libpango1.0-dev \
    libmagic1 \
    gir1.2-pango-1.0 \
    gir1.2-rsvg-2.0 \
    libpython3-dev && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

#RUN wget -q https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py
RUN curl -JO http://use.yt/upload/9e31e267 && python3 get-pip.py

ENV PYCAIRO=pycairo-1.11.0
RUN cd /tmp && \
  wget https://github.com/pygobject/pycairo/releases/download/v1.11.0/$PYCAIRO.tar.gz -O $PYCAIRO.tar.gz && \
  tar -xzf $PYCAIRO.tar.gz && \
  cd $PYCAIRO && \
  python3 setup.py install && \
  cd /tmp && \
  rm -rf /tmp/$PYCAIRO

WORKDIR /girder
COPY girder /girder/girder
COPY clients /girder/clients
COPY scripts /girder/scripts
COPY grunt_tasks /girder/grunt_tasks
COPY Gruntfile.js /girder/Gruntfile.js
COPY setup.py /girder/setup.py
COPY package.json /girder/package.json
COPY README.rst /girder/README.rst
COPY plugins /girder/plugins
COPY pytest_girder /girder/pytest_girder

RUN python3 -m pip install -U setuptools==49.6.0   # 50.0.0 breaks entrypoints
RUN python3 -m pip install --no-cache-dir -q \
  -r plugins/wholetale/requirements.txt \
  -e .[plugins,sftp]   # Most of the plugins is grabbed via plugins/.gitignore
RUN python3 -m pip install -U pyOpenSSL
ENV NPM_CONFIG_LOGLEVEL=warn NPM_CONFIG_COLOR=false NPM_CONFIG_PROGRESS=false
RUN girder-install web \
  --plugins=oauth,gravatar,jobs,worker,wt_data_manager,wholetale,wt_home_dir,virtual_resources,wt_versioning \
  && rm -rf /root/.npm /tmp/npm* /girder/node_modules

# RUN python3 -c "import nltk; nltk.download('wordnet')"
# RUN python3 -m spacy download en

COPY girder.local.cfg.dev /girder/girder/conf/girder.local.cfg

# See http://click.pocoo.org/5/python3/#python-3-surrogate-handling for more detail on
# why this is necessary.
ENV LC_ALL=C.UTF-8 LANG=C.UTF-8
RUN python3 -m pip install ipython

RUN girder-worker-config set celery backend redis://redis/ && \
  girder-worker-config set celery broker redis://redis/ && \
  girder-worker-config set girder_worker tmp_root /tmp

# Temporary fix for kombu
RUN sed \
  -e 's/return decode(data/&.decode("utf-8")/' \
  -i /usr/local/lib/python3.7/dist-packages/kombu/serialization.py

# install GCP client
ENV GCP_URL=https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz
RUN wget -qO- $GCP_URL | tar xz -C /opt && \
  mv /opt/globusconnectpersonal-* /opt/globusconnectpersonal

RUN groupadd -r girder \
  && useradd --no-log-init -s /bin/bash -p $(openssl rand -base64 32) -m -r -g girder girder \
  && usermod -U girder \
  && chown girder:girder -R /girder

ENV GOSU_USER=0:0
COPY ./docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["girder", "serve"]
