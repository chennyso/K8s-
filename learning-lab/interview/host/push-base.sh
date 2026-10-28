set -euo pipefail
docker tag python:3.13-slim-bookworm 192.168.204.1:15000/learning/python:3.13-slim-bookworm
docker push 192.168.204.1:15000/learning/python:3.13-slim-bookworm
