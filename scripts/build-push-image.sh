#!/usr/bin/env bash
# Build the scanner image and push to ECR. Usage: NAME_SUFFIX=angger26 ./scripts/build-push-image.sh
set -euo pipefail
REGION="${AWS_REGION:-us-east-1}"; PREFIX="${PREFIX:-sentinel}"
ACCT="$(aws sts get-caller-identity --query Account --output text)"
REPO="${PREFIX}-scanner"
REGISTRY="${ACCT}.dkr.ecr.${REGION}.amazonaws.com"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY"
docker build -t "${REPO}:latest" "$(dirname "$0")/../docker"
docker tag "${REPO}:latest" "${REGISTRY}/${REPO}:latest"
docker push "${REGISTRY}/${REPO}:latest"
echo "Pushed ${REGISTRY}/${REPO}:latest"
