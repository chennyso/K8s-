#!/bin/sh
set -eu
: "${CI_REGISTRY:?}"
: "${CI_REGISTRY_USER:?}"
: "${CI_REGISTRY_PASSWORD:?}"
: "${CI_REGISTRY_IMAGE:?}"
: "${CI_COMMIT_SHA:?}"
: "${CI_PIPELINE_ID:?}"
export DOCKER_CONFIG="$CI_PROJECT_DIR/.docker"
mkdir -p "$DOCKER_CONFIG"
chmod 700 "$DOCKER_CONFIG"
authentication=$(printf '%s:%s' "$CI_REGISTRY_USER" "$CI_REGISTRY_PASSWORD" | base64 | tr -d '\n')
umask 077
printf '{"auths":{"%s":{"auth":"%s"}}}\n' "$CI_REGISTRY" "$authentication" > "$DOCKER_CONFIG/config.json"
trap 'rm -f "$DOCKER_CONFIG/config.json"' EXIT
buildctl-daemonless.sh build \
  --frontend dockerfile.v0 \
  --local context=. --local dockerfile=. \
  --opt platform=linux/amd64 \
  --opt build-arg:APP_VERSION="$CI_COMMIT_SHA" \
  --output type=image,name="$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA-$CI_PIPELINE_ID",push=true \
  --metadata-file build-metadata.json
