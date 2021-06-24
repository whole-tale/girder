FROM node:12-buster
MAINTAINER Kacper Kowalik <xarthisius.kk@gmail.com>

EXPOSE 8080

ENV PYTHON_VERSION 3.9.5
ENV GPG_KEY E3FF2839C048B25C084DEBE9B26995E310250568

RUN apt-get update -qqy && \
  apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    git \
    vim \
    gosu \
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

RUN set -ex \
  \
  && cd /tmp \
	&& wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz" \
	&& wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc" \
	&& export GNUPGHOME="$(mktemp -d)" \
	&& gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$GPG_KEY" \
	&& gpg --batch --verify python.tar.xz.asc python.tar.xz \
	&& { command -v gpgconf > /dev/null && gpgconf --kill all || :; } \
	&& rm -rf "$GNUPGHOME" python.tar.xz.asc \
	&& mkdir -p /usr/src/python \
	&& tar -xJC /usr/src/python --strip-components=1 -f python.tar.xz \
	&& rm python.tar.xz \
	\
	&& cd /usr/src/python \
	&& gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)" \
	&& ./configure \
		--build="$gnuArch" \
		--enable-loadable-sqlite-extensions \
		--enable-optimizations \
		--enable-option-checking=fatal \
		--enable-shared \
		--with-system-expat \
		--with-system-ffi \
		--without-ensurepip \
	&& make -j "$(nproc)" \
	&& make altinstall \
  && cd /tmp \
	&& rm -rf /usr/src/python \
	\
	&& find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name '*.a' \) \) \
		\) -exec rm -rf '{}' + \
	\
	&& ldconfig

# install GCP client
ENV GCP_URL=https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz
RUN wget -qO- $GCP_URL | tar xz -C /opt && \
  mv /opt/globusconnectpersonal-* /opt/globusconnectpersonal

RUN groupadd -r girder \
  && useradd --no-log-init -s /bin/bash -p $(openssl rand -base64 32) -m -r -g girder girder \
  && usermod -U girder

COPY --chown=girder:girder . /girder/
WORKDIR /girder

RUN virtualenv -p /usr/local/bin/python3.9 /girder/venv
ENV VIRTUAL_ENV=/girder/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python -m pip install --no-cache-dir -q \
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

ENV GOSU_USER=0:0
COPY ./docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["girder", "serve"]
