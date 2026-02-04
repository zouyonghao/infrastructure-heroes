#!/usr/bin/env python3
"""
Script to update project logos with accessible URLs.
Uses well-known CDN sources and official brand resources.
"""

import os
import re

# Logo mappings - using reliable sources like GitHub, official sites, or CDNs
LOGO_URLS = {
    # Core Infrastructure
    'linux-kernel': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/linux/linux-original.svg',
    'glibc': 'https://www.gnu.org/graphics/heckert_gnu.transp.small.png',
    'busybox': 'https://busybox.net/images/busybox1.png',
    'openssl': 'https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/openssl.svg',
    'zlib': '',  # No standard logo
    'curl': 'https://curl.se/logo/curl-logo.svg',
    'openssh': '',  # No standard logo
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
    'scylladb': '',  # No standard SVG
    'influxdb': 'https://raw.githubusercontent.com/influxdata/branding/master/logos/influxdb/influxdb-logo--symbol--pool.svg',
    'timescaledb': '',  # No standard SVG
    'vitess': 'https://vitess.io/img/logos/vitess.png',

    # Container & Orchestration
    'docker-moby': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/docker/docker-original.svg',
    'kubernetes': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/kubernetes/kubernetes-original.svg',
    'containerd': 'https://containerd.io/img/logos/icon/black/containerd-icon-black.svg',
    'helm': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/helm/helm-original.svg',
    'istio': 'https://istio.io/latest/img/istio-whitelogo-bluebackground-framed.svg',
    'envoy': '',  # No standard SVG logo

    # CI/CD & DevOps
    'terraform': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/terraform/terraform-original.svg',
    'ansible': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/ansible/ansible-original.svg',
    'jenkins': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/jenkins/jenkins-original.svg',
    'argocd': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/argocd/argocd-original.svg',
    'flux': '',  # No standard logo
    'actions-runner': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/github/github-original.svg',

    # Monitoring & Observability
    'prometheus': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/prometheus/prometheus-original.svg',
    'grafana': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/grafana/grafana-original.svg',
    'jaeger': '',  # No devicon
    'opentelemetry': 'https://opentelemetry.io/img/logos/opentelemetry-logo-nav.png',
    'loki': '',  # No standard logo
    'fluentd': '',  # No standard logo
    'logstash': '',  # No standard logo

    # Message Queues
    'kafka': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/apachekafka/apachekafka-original.svg',
    'rabbitmq': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/rabbitmq/rabbitmq-original.svg',
    'nats': '',  # No standard logo

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
    'apt': '',  # No standard logo
    'webpack': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/webpack/webpack-original.svg',
    'babel': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/babel/babel-original.svg',
    'eslint': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/eslint/eslint-original.svg',
    'prettier': '',  # No devicon

    # Web Frameworks
    'react': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/react/react-original.svg',
    'vuejs': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/vuejs/vuejs-original.svg',
    'angular': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/angular/angular-original.svg',
    'svelte': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/svelte/svelte-original.svg',
    'nextjs': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/nextjs/nextjs-original.svg',
    'django': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/django/django-plain.svg',
    'flask': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/flask/flask-original.svg',
    'rails': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/rails/rails-plain.svg',
    'spring': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/spring/spring-original.svg',
    'fastapi': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/fastapi/fastapi-original.svg',
    'expressjs': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/express/express-original.svg',

    # Data Processing
    'spark': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/apachespark/apachespark-original.svg',
    'flink': '',  # No devicon
    'airflow': 'https://raw.githubusercontent.com/devicons/devicon/master/icons/apacheairflow/apacheairflow-original.svg',

    # Misc Infrastructure
    'etcd': '',  # No standard logo
    'consul': '',  # No devicon
    'vault': '',  # No devicon
    'zookeeper': '',  # No devicon
    'coredns': '',  # No standard logo
    'bind': '',  # No standard logo
    'certbot': '',  # No standard logo
    'letsencrypt': 'https://letsencrypt.org/images/letsencrypt-logo-horizontal.svg',
    'imagemagick': '',  # No standard logo
    'ffmpeg': 'https://ffmpeg.org/img/ffmpeg-logo.png',
    'grpc': '',  # No devicon
    'protobuf': '',  # No devicon

    # Storage
    'minio': '',  # No devicon
    'ceph': '',  # No devicon
    'glusterfs': '',  # No standard logo
    'rook': '',  # No standard logo

    # Caching
    'memcached': '',  # No devicon
    'varnish': '',  # No standard logo
    'squid': '',  # No standard logo
}

def update_project_logo(filepath, logo_url):
    """Update the logo field in a project markdown file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace the logo line
    new_content = re.sub(
        r"^logo = '[^']*'",
        f"logo = '{logo_url}'",
        content,
        flags=re.MULTILINE
    )

    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    projects_dir = '/home/zyh/infrastructure-heroes/content/projects'

    updated = 0
    skipped = 0

    for filename in os.listdir(projects_dir):
        if not filename.endswith('.md') or filename == '_index.md':
            continue

        project_name = filename.replace('.md', '')
        filepath = os.path.join(projects_dir, filename)

        if project_name in LOGO_URLS:
            logo_url = LOGO_URLS[project_name]
            if update_project_logo(filepath, logo_url):
                print(f"Updated: {project_name} -> {logo_url[:60]}..." if logo_url else f"Cleared: {project_name}")
                updated += 1
            else:
                skipped += 1
        else:
            print(f"No mapping for: {project_name}")

    print(f"\nDone! Updated: {updated}, Skipped: {skipped}")

if __name__ == '__main__':
    main()
