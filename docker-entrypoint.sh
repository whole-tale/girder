#!/bin/bash
# Author: Jonathan Meyer <jon@gisjedi.com>
# Source: https://github.com/gisjedi/gosu-entrypoint
# Version: master

set -e
IFS=: read GOSU_UID GOSU_GID DOCKER_GROUP <<<"${GOSU_USER}"

# If GOSU_CHOWN environment variable set, recursively chown all specified directories 
# to match the user:group set in GOSU_USER environment variable.
if [ -n "$GOSU_CHOWN" ]; then
    for DIR in $GOSU_CHOWN
    do
        chown -R $GOSU_UID:$GOSU_GID $DIR
    done
fi  

# If GOSU_USER environment variable set to something other than 0:0 (root:root),
# become user:group set within and exec command passed in args
if [ "$GOSU_USER" != "0:0" ]; then
    groupadd -g $DOCKER_GROUP docker || /bin/true
    gpasswd -a girder docker || /bin/true
    usermod -g $GOSU_GID girder || /bin/true
    exec gosu $GOSU_UID "$@"
fi

# If GOSU_USER was 0:0 exec command passed in args without gosu (assume already root)
exec "$@"
