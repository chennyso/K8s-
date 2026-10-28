set -eu
printf '%s\n' "$$" > /data/writer.pid
trap 'printf "writer 收到终止信号，进程=%s\n" "$$"; exit 0' TERM INT
while true; do
  count=$(cat /data/counter)
  count=$((count + 1))
  printf '%s\n' "$count" > /data/counter
  printf '{"pod":"%s","pod_ip":"%s","node":"%s","writer_pid":%s,"heartbeats":%s,"time":"%s"}\n' \
    "$POD_NAME" "$POD_IP" "$NODE_NAME" "$$" "$count" "$(date -u +%FT%TZ)" > /data/status.next
  mv /data/status.next /data/status.json
  printf '# HELP pod_lab_heartbeats_total Writer heartbeat iterations.\n# TYPE pod_lab_heartbeats_total counter\npod_lab_heartbeats_total{pod="%s"} %s\n' "$POD_NAME" "$count" > /data/metrics.next
  mv /data/metrics.next /data/metrics.txt
  printf 'writer pod=%s pid=%s heartbeat=%s\n' "$POD_NAME" "$$" "$count"
  sleep 2
done
