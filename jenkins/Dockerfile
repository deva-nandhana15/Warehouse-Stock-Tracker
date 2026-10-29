FROM docker:28.5.1-cli@sha256:9190b0613792e658a7783cf14b2d5ace5941bb68ede7276922ea36ee457d76ad AS dockercli
FROM jenkins/jenkins:2.580.2-jdk21@sha256:74401de6a6f92e1afe1b02d1c8e3d0c33f263bfb5275dd8813f9150355f2367b

USER root
# Versions verified from the signed Debian repositories in the pinned base image.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3=3.13.5-1 python3-venv=3.13.5-1 nodejs=20.19.2+dfsg-1+deb13u3 npm=9.2.0~ds1-3 \
 && rm -rf /var/lib/apt/lists/*
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=dockercli /usr/local/libexec/docker/cli-plugins/ /usr/local/libexec/docker/cli-plugins/
COPY assets/ /tmp/warehouse-tools/
RUN cd /tmp/warehouse-tools \
 && sha256sum -c SHA256SUMS \
 && tar -xzf trivy_0.76.1_Linux-64bit.tar.gz -C /usr/local/bin trivy \
 && tar -xzf gitleaks_8.30.1_linux_x64.tar.gz -C /usr/local/bin gitleaks \
 && unzip -q terraform_1.17.0_linux_amd64.zip terraform -d /usr/local/bin \
 && chmod 755 /usr/local/bin/trivy /usr/local/bin/gitleaks /usr/local/bin/terraform \
 && rm -rf /tmp/warehouse-tools

USER jenkins
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt --latest false
COPY --chown=jenkins:jenkins init.groovy.d/ /usr/share/jenkins/ref/init.groovy.d/
