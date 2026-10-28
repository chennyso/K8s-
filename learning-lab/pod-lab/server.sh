set -eu
touch /data/live
printf '%s\n' "$$" > /data/server.pid
exec httpd -f -v -p 8080 -h /data
