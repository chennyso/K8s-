external_url 'http://192.168.204.1:18080'
nginx['listen_port'] = 18080
nginx['listen_https'] = false
gitlab_rails['gitlab_shell_ssh_port'] = 12222
gitlab_rails['gitlab_signup_enabled'] = false
gitlab_rails['smtp_enable'] = false
letsencrypt['enable'] = false
prometheus['enable'] = false
alertmanager['enable'] = false
puma['worker_processes'] = 2
sidekiq['concurrency'] = 10
postgresql['shared_buffers'] = '256MB'
gitlab_rails['time_zone'] = 'Asia/Shanghai'
