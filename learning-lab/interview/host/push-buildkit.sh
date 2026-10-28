set -euo pipefail
docker tag moby/buildkit:v0.25.1-rootless 192.168.204.1:15000/learning/buildkit:v0.25.1-rootless
docker push 192.168.204.1:15000/learning/buildkit:v0.25.1-rootless
