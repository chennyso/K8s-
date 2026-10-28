set -euo pipefail
cd /var/lib/interview-lab
install -d -m 750 certs registry/data seaweed/data
chown 1000:1000 seaweed/data secrets/s3.json
openssl genrsa -out certs/ca.key 3072
openssl req -x509 -new -key certs/ca.key -sha256 -days 3650 -config host/ca.cnf -out certs/ca.crt
openssl genrsa -out certs/registry.key 2048
openssl req -new -key certs/registry.key -config host/registry.cnf -out certs/registry.csr
openssl x509 -req -in certs/registry.csr -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial -out certs/registry.crt -days 365 -sha256 -extfile host/registry.cnf -extensions server
chmod 600 certs/*.key
docker load -i "${1:-host-images.tar.gz}"
docker run -d --name interview-registry --restart unless-stopped --memory 256m --cpus 1 -p 192.168.204.1:15000:5000 -v "$PWD/registry/data:/var/lib/registry" -v "$PWD/certs:/certs:ro" -v "$PWD/secrets:/auth:ro" -v "$PWD/host/registry.yaml:/etc/distribution/config.yml:ro" registry:3
docker run -d --name interview-s3 --restart unless-stopped --memory 1g --cpus 2 -p 192.168.204.1:18333:8333 -v "$PWD/seaweed/data:/data" -v "$PWD/secrets/s3.json:/etc/seaweedfs/s3.json:ro" chrislusf/seaweedfs:latest server -dir=/data -ip=127.0.0.1 -ip.bind=0.0.0.0 -master.volumeSizeLimitMB=1024 -volume.max=8 -filer -s3 -s3.port=8333 -s3.config=/etc/seaweedfs/s3.json
docker inspect interview-registry interview-s3 --format '{{.Name}} {{.State.Status}}'
