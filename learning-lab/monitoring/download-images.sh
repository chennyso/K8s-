set -euo pipefail
cd "$(dirname "$0")"
images=()
while IFS= read -r image; do
  docker pull --platform linux/amd64 "$image"
  images+=("$image")
done < images.txt
docker save --platform linux/amd64 "${images[@]}" | gzip -1 > monitoring-images.tar.gz
shasum -a 256 monitoring-images.tar.gz > monitoring-images.sha256
