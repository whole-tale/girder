FROM node:12-bullseye
MAINTAINER Kacper Kowalik <xarthisius.kk@gmail.com>

EXPOSE 8080

RUN apt-get update -qqy && \
  apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    git \
    gosu \
    vim \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libssl-dev \
    libsqlite3-dev \
    libreadline-dev \
    libffi-dev \
    xsltproc \
    curl \
    libffi-dev \
    libfuse-dev \
    libsasl2-dev \
    libssl-dev \
    libldap2-dev \
    libmagic1 \
    libpython3-dev \
    virtualenv \
    python3-virtualenv \
    libbz2-dev && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

# install GCP client
ENV GCP_LATEST=https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz
ENV GCP_URL=https://github.com/whole-tale/globus_handler/releases/download/gcp-3.0.4/globusconnectpersonal-3.0.4.tar.gz
RUN wget -qO- $GCP_URL | tar xz -C /opt
# Update GCP certs
RUN wget -qO- $GCP_LATEST | tar xz -C /tmp \
  && cd /tmp//globusconnectpersonal* \
  && mv etc/ca/* /opt/globusconnectpersonal/etc/ca/ \
  && rm -rf /tmp/globusconnectpersonal*

RUN userdel node \
  && groupadd -g 1000 girder \
  && useradd -u 1000 -g 1000 --no-log-init -s /bin/bash -p $(openssl rand -base64 32) -m -r girder \
  && usermod -U girder

COPY --chown=girder:girder . /girder/
WORKDIR /girder

RUN virtualenv -p /usr/bin/python3.9 /girder/venv
ENV VIRTUAL_ENV=/girder/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python -m pip install --no-cache-dir \
  -r plugins/wholetale/requirements.txt \
  -e .[plugins,sftp]   # Most of the plugins is grabbed via plugins/.gitignore
RUN python -m pip install --no-cache-dir -U pyOpenSSL
ENV NPM_CONFIG_LOGLEVEL=warn NPM_CONFIG_COLOR=false NPM_CONFIG_PROGRESS=false
RUN girder-install web \
  --plugins=oauth,gravatar,jobs,worker,wt_data_manager,wholetale,wt_home_dir,virtual_resources,wt_versioning \
  && rm -rf /home/girder/.npm /tmp/npm* /girder/node_modules

COPY girder.local.cfg.dev /girder/girder/conf/girder.local.cfg

# See http://click.pocoo.org/5/python3/#python-3-surrogate-handling for more detail on
# why this is necessary.
ENV LC_ALL=C.UTF-8 LANG=C.UTF-8
RUN python -m pip install --no-cache-dir ipython

RUN girder-worker-config set celery backend redis://redis/ && \
  girder-worker-config set celery broker redis://redis/ && \
  girder-worker-config set girder_worker tmp_root /tmp

RUN sed -i ${VIRTUAL_ENV}/lib/python3.9/site-packages/girder_worker/task.py \
  -e "/serializer/ s/girder_io/json/"

ENV GOSU_USER=0:0
COPY ./docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["girder", "serve"]
