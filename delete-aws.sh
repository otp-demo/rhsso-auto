#!/bin/bash
source .env

echo "Configure AWS credentials..."
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}


aws iam delete-saml-provider --profile test-sso --saml-provider-arn arn:aws:iam::168025195644:saml-provider/demo
aws iam detach-role-policy --role-name READ_ONLY_USER_ROLE --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
aws iam delete-role --role-name READ_ONLY_USER_ROLE