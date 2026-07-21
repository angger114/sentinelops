# SentinelOps deep-scan image: OPA Conftest (real OSS policy engine) + AWS CLI.
FROM alpine:3.20

ARG CONFTEST_VERSION=0.56.0
RUN apk add --no-cache aws-cli ca-certificates curl tar && \
    curl -sSL "https://github.com/open-policy-agent/conftest/releases/download/v${CONFTEST_VERSION}/conftest_${CONFTEST_VERSION}_Linux_x86_64.tar.gz" \
      | tar -xz -C /usr/local/bin conftest && \
    chmod +x /usr/local/bin/conftest && \
    adduser -D -u 1000 scanner

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER 1000
ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
