set -euo pipefail
cd /var/lib/interview-lab
docker load -i "${1:-gitlab-images.tar.gz}"
install -d -m 750 gitlab/config gitlab/logs gitlab/data
install -m 600 host/gitlab.rb gitlab/config/gitlab.rb
docker run -d --name interview-gitlab --hostname gitlab.204.test \
  --restart unless-stopped --memory 16g --cpus 8 --shm-size 256m \
  --publish 192.168.204.1:18080:18080 \
  --publish 192.168.204.1:12222:22 \
  --env-file secrets/gitlab.env \
  --volume /var/lib/interview-lab/gitlab/config:/etc/gitlab \
  --volume /var/lib/interview-lab/gitlab/logs:/var/log/gitlab \
  --volume /var/lib/interview-lab/gitlab/data:/var/opt/gitlab \
  gitlab/gitlab-ce:19.4.3-ce.0
