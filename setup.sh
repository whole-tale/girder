#/bin/sh
girder-worker-config set celery backend redis://${REDIS_MASTER_SERVICE_HOST}:${REDIS_MASTER_SERVICE_PORT}/
girder-worker-config set celery broker redis://${REDIS_MASTER_SERVICE_HOST}:${REDIS_MASTER_SERVICE_PORT}/
