# SentinelOps - Starter Kit

Autonomous Remediation & Audit-Lake Automation Platform (DevOps & Cloud Automation).
Build the **CloudFormation** stack and the **Step Functions** workflows, wire up CI/CD, and pass the
end-to-end verification. See `MODULE.docx` for the full spec and marking scheme.

## Provided (do not rewrite unless asked)
```
src/                     Lambda source for 8 functions + shared layer (sentinel_common)
k8s/                     Kubernetes manifests (namespace, SA, RBAC, ConfigMap policy, Jobs)
docker/                  OPA Conftest scanner image (Dockerfile + entrypoint + Rego policy)
frontend/                static Amplify compliance dashboard
appspec/                 CodeDeploy Blue/Green AppSpec (Lambda)
.github/workflows/       6-job GitHub Actions pipeline
scripts/package.sh       Zip src + upload to the artifacts bucket
events/                  Test payloads (finding / approval / init)
```

## You build
1. **CloudFormation** for all infra EXCEPT Step Functions: **KMS CMK**, DynamoDB (status + resource GSIs,
   SSE-KMS), S3 (scan-input + artifacts + target), **AWS Backup vault**, SNS, SQS, Secrets/SSM,
   8 Lambdas + layer + `live` alias, API Gateway, EventBridge, CodeDeploy, CloudWatch. Everything on
   **LabRole** - create no IAM roles. No VPC (fully public serverless).
2. **Two state machines in the Step Functions console (Workflow Studio)**:
   `sentinel-remediation-orchestrator` (STANDARD) and `sentinel-enrichment-express` (EXPRESS).
   The reference ASL in `solution/asl/` is what you paste into the Code view / self-check against.
3. **EKS Auto Mode deep-scan**: build/push the Conftest scanner image to ECR, apply the `k8s/`
   manifests, and let Step Functions run the DeepScan + Verify Jobs via `eks:runJob.sync`.
4. **Amplify dashboard**: publish `frontend/` and point it at `GET /report`.

## Architecture at a glance (distinct from a plain order-workflow)
Finding -> ingest+idempotency -> classify -> **Parallel** [Express enrichment `.sync` | **DynamoDB Query**
repeat-offender on the resource GSI] -> **Distributed Map** compliance sweep -> **task-token** human
approval -> (CRITICAL) **EKS deep-scan Job** (OPA Conftest, `eks:runJob.sync`) -> **AWS Backup** safety
snapshot -> Blue/Green remediate Lambda applies **S3 PutPublicAccessBlock** -> **EKS verify Job** ->
record (DynamoDB) -> EventBridge -> SNS -> **Amplify** dashboard (`GET /report`).

## Order of operations
1. `aws s3 mb s3://sentinel-artifacts-<suffix>` then `ARTIFACTS_BUCKET=... ./scripts/package.sh`.
2. Deploy the CloudFormation stack `sentinelops-infra`.
3. Build both state machines in Workflow Studio (or run `solution/scripts/deploy-stepfunctions.sh`),
   then store the orchestrator ARN in SSM `/sentinel/stepfunctions/orchestrator_arn`.
4. Invoke `sentinel-fn-init` (`events/init-payload.json`) to seed findings, repeat-offender history, and Map inventory.
5. `POST /findings` and walk the workflow, including the approval pause.

## Learner Lab guardrails
- Region **us-east-1**. **LabRole only** (no `iam:CreateRole`). Fully serverless (no EC2/VPC needed).
- **X-Ray is bonus only** - LabRole grants no `xray:*`. Core observability = CloudWatch.

> Full reference implementation in `solution/` - use it to self-check after your own attempt.
