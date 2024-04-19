FROM ubuntu:22.04
MAINTAINER Kacper Kowalik <xarthisius.kk@gmail.com>

EXPOSE 8080

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    GCP_LATEST=https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz \
    GCP_URL=https://github.com/whole-tale/globus_handler/releases/download/gcp-3.0.4/globusconnectpersonal-3.0.4.tar.gz \
    NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_COLOR=false \
    NPM_CONFIG_PROGRESS=false \
    GOSU_USER=0:0 \
    VIRTUAL_ENV=/girder/venv


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
    wget \
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

RUN curl -LJ https://github.com/krallin/tini/releases/download/v0.19.0/tini -o /sbin/tini && \
    chmod +x /sbin/tini

# Add girder user
RUN groupadd -g 1000 girder \
  && useradd -u 1000 -g 1000 --no-log-init -s /bin/bash -p $(openssl rand -base64 32) -m -r girder \
  && usermod -U girder

ENV NVM_DIR /home/girder/.nvm
ENV NODE_VERSION 14

# install GCP client
RUN wget -qO- $GCP_URL | tar xz -C /opt
# Update GCP certs
RUN wget -qO- $GCP_LATEST | tar xz -C /tmp \
  && cd /tmp//globusconnectpersonal* \
  && mv etc/ca/* /opt/globusconnectpersonal/etc/ca/ \
  && rm -rf /tmp/globusconnectpersonal*

# Install NodeJS
USER girder
WORKDIR /tmp
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash \
  && . $NVM_DIR/nvm.sh && \
  nvm install $NODE_VERSION && \
  nvm alias default $NODE_VERSION && \
  nvm use default

COPY --chown=girder:girder . /girder/
WORKDIR /girder

RUN virtualenv -p /usr/bin/python3.10 ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:/usr/local/node:${PATH}"

RUN python -m pip install --no-cache-dir \
  -r plugins/wholetale/requirements.txt \
  -e .[plugins,sftp]   # Most of the plugins is grabbed via plugins/.gitignore
RUN python -m pip install --no-cache-dir -U pyOpenSSL
RUN . ~/.nvm/nvm.sh && \
  girder-install web \
  --plugins=oauth,gravatar,jobs,worker,wt_data_manager,wholetale,wt_home_dir,virtual_resources,wt_versioning,sem_viewer,table_view,homepage,image_previews \
  && rm -rf /home/girder/.npm /tmp/npm* /girder/node_modules

COPY girder.local.cfg.dev /girder/girder/conf/girder.local.cfg

# See http://click.pocoo.org/5/python3/#python-3-surrogate-handling for more detail on
# why this is necessary.
RUN python -m pip install --no-cache-dir ipython

RUN girder-worker-config set celery backend redis://redis/ && \
  girder-worker-config set celery broker redis://redis/ && \
  girder-worker-config set girder_worker tmp_root /tmp

RUN sed -i ${VIRTUAL_ENV}/lib/python3.10/site-packages/girder_worker/task.py \
  -e "/serializer/ s/girder_io/json/"

COPY ./docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["girder", "serve"]
