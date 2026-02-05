#!/usr/bin/env python3
"""
Script to check if logo URLs are accessible.
"""

import requests

# Copy the LOGO_URLS from update_logos.py
LOGO_URLS = {
    # Core Infrastructure
    'linux-kernel': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/linux/linux-original.svg',
    'glibc': 'https://www.gnu.org/graphics/heckert_gnu.transp.small.png',
    'busybox': 'https://busybox.net/images/busybox1.png',
    'openssl': 'https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/openssl.svg',
    'zlib': 'https://zlib.net/images/zlib3d-b1.png',
    'curl': 'https://curl.se/logo/curl-logo.svg',
    'openssh': 'https://www.openssh.org/images/openssh.gif',
    'gnupg': 'https://gnupg.org/share/logo-gnupg-light-purple-bg.png',

    # Web Servers
    'nginx': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/nginx/nginx-original.svg',
    'apache-httpd': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/apache/apache-original.svg',
    'caddy': 'https://caddyserver.com/resources/images/caddy-logo.svg',
    'traefik': 'https://raw.githubusercontent.com/traefik/traefik/master/docs/content/assets/img/traefik.logo.png',
    'haproxy': 'https://www.haproxy.com/img/HAProxyLogo.png',

    # Databases
    'postgresql': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/postgresql/postgresql-original.svg',
    'mysql': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/mysql/mysql-original.svg',
    'mariadb': 'https://mariadb.com/wp-content/uploads/2019/11/mariadb-logo_blue-transparent.png',
    'sqlite': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/sqlite/sqlite-original.svg',
    'mongodb': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/mongodb/mongodb-original.svg',
    'redis': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/redis/redis-original.svg',
    'elasticsearch': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/elasticsearch/elasticsearch-original.svg',
    'cassandra': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/cassandra/cassandra-original.svg',
    'neo4j': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/neo4j/neo4j-original.svg',
    'cockroachdb': 'https://www.cockroachlabs.com/img/CockroachLabs_Logo_Mark-lightbackground.svg',
    'tidb': 'https://raw.githubusercontent.com/pingcap/tidb/master/docs/logo_with_text.png',
    'clickhouse': 'https://clickhouse.com/images/ch_gh_logo.svg',
    'scylladb': 'https://www.scylladb.com/wp-content/uploads/scylla-logo-horizontal-RGB.png',
    'influxdb': 'https://raw.githubusercontent.com/influxdata/branding/master/logos/influxdb/influxdb-logo--symbol--pool.svg',
    'timescaledb': 'https://www.timescale.com/static/images/timescale-logo.svg',
    'vitess': 'https://vitess.io/img/logos/vitess.png',

    # Container & Orchestration
    'docker-moby': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/docker/docker-original.svg',
    'kubernetes': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/kubernetes/kubernetes-original.svg',
    'containerd': 'https://containerd.io/img/logos/icon/black/containerd-icon-black.svg',
    'helm': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/helm/helm-original.svg',
    'istio': 'https://istio.io/latest/img/istio-whitelogo-bluebackground-framed.svg',
    'envoy': 'https://www.envoyproxy.io/img/envoy-logo.svg',

    # CI/CD & DevOps
    'terraform': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/terraform/terraform-original.svg',
    'ansible': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/ansible/ansible-original.svg',
    'jenkins': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/jenkins/jenkins-original.svg',
    'argocd': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/argocd/argocd-original.svg',
    'flux': 'https://fluxcd.io/img/flux-horizontal-color.png',
    'actions-runner': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/github/github-original.svg',

    # Monitoring & Observability
    'prometheus': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/prometheus/prometheus-original.svg',
    'grafana': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/grafana/grafana-original.svg',
    'jaeger': 'https://www.jaegertracing.io/img/jaeger-logo.png',
    'opentelemetry': 'https://opentelemetry.io/img/logos/opentelemetry-logo-nav.png',
    'loki': 'https://grafana.com/static/img/logos/loki-logo.svg',
    'fluentd': 'https://www.fluentd.org/images/logo/Fluentd_square.png',
    'logstash': 'https://raw.githubusercontent.com/elastic/logstash/master/docs/static/images/logstash-logo.png',

    # Message Queues
    'kafka': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/apachekafka/apachekafka-original.svg',
    'rabbitmq': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/rabbitmq/rabbitmq-original.svg',
    'nats': 'https://nats.io/img/logo.png',

    # Programming Languages & Runtimes
    'python': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg',
    'nodejs': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/nodejs/nodejs-original.svg',
    'go': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/go/go-original.svg',
    'rust': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/rust/rust-original.svg',
    'ruby': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/ruby/ruby-original.svg',
    'php': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/php/php-original.svg',
    'typescript': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/typescript/typescript-original.svg',
    'deno': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/denojs/denojs-original.svg',
    'bun': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/bun/bun-original.svg',

    # Compilers & Build Tools
    'llvm': 'https://llvm.org/img/LLVM-Logo-Derivative-1.png',
    'git': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/git/git-original.svg',
    'cargo': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/rust/rust-original.svg',
    'npm': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/npm/npm-original-wordmark.svg',
    'pip': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg',
    'homebrew': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/homebrew/homebrew-original.svg',
    'apt': '',
    'webpack': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/webpack/webpack-original.svg',
    'babel': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/babel/babel-original.svg',
    'eslint': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/eslint/eslint-original.svg',
    'prettier': 'https://raw.githubusercontent.com/prettier/prettier-logo/master/images/prettier-logo-dark.svg',

    # Web Frameworks
    'react': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/react/react-original.svg',
    'vuejs': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/vuejs/vuejs-original.svg',
    'angular': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/angular/angular-original.svg',
    'svelte': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/svelte/svelte-original.svg',
    'nextjs': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/nextjs/nextjs-original.svg',
    'django': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/django/django-original.svg',
    'flask': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/flask/flask-original.svg',
    'rails': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/rails/rails-original.svg',
    'spring': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/spring/spring-original.svg',
    'fastapi': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/fastapi/fastapi-original.svg',
    'expressjs': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/express/express-original.svg',

    # Data Processing
    'spark': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/apachespark/apachespark-original.svg',
    'flink': 'https://flink.apache.org/img/logo/png/1000/flink_logo_1000.png',
    'airflow': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/apacheairflow/apacheairflow-original.svg',

    # Misc Infrastructure
    'etcd': 'https://etcd.io/img/logo-etcd.svg',
    'consul': 'https://www.consul.io/img/logo-consul.svg',
    'vault': 'https://www.vaultproject.io/img/logo-vault.svg',
    'zookeeper': 'https://zookeeper.apache.org/images/zookeeper_small.gif',
    'coredns': 'https://coredns.io/images/CoreDNS_Colour_Vertical.png',
    'bind': 'https://www.isc.org/wp-content/themes/iscorg/images/bind-logo.png',
    'certbot': 'https://certbot.eff.org/images/certbot-logo-1.png',
    'letsencrypt': 'https://letsencrypt.org/images/letsencrypt-logo-horizontal.svg',
    'imagemagick': 'https://imagemagick.org/image/wizard.png',
    'ffmpeg': 'https://ffmpeg.org/img/ffmpeg-logo.png',
    'grpc': 'https://grpc.io/img/logos/grpc-logo.png',
    'protobuf': 'https://developers.google.com/protocol-buffers/docs/images/protobuf-logo.png',

    # Storage
    'minio': 'https://min.io/resources/img/logo/MINIO_Bird.png',
    'ceph': 'https://ceph.io/wp-content/themes/ceph/images/ceph-logo.png',
    'glusterfs': 'https://www.gluster.org/wp-content/uploads/2016/03/gluster-logo.png',
    'rook': 'https://rook.io/img/rook-logo.png',

    # Caching
    'memcached': 'https://memcached.org/images/memcached-logo.png',
    'varnish': 'https://varnish-cache.org/_images/varnish-logo.png',
    'squid': 'https://www.squid-cache.org/Images/squid-logo.png',
}

def check_url(url):
    if not url:
        return False
    try:
        response = requests.get(url, timeout=10, stream=True)
        response.close()
        return response.status_code == 200
    except:
        return False

for project, url in LOGO_URLS.items():
    if url and not check_url(url):
        print(f"Broken: {project} -> {url}")
    elif not url:
        print(f"Empty: {project}")

print("Done checking.")