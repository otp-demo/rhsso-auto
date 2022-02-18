#!/bin/bash
# source .env

source ../../utils.sh

wait_for_preprocessing

function print_failure() 
{
    if [[ $? -ne 0 ]]; then
        echo $1
        exit 1
    fi
}

if [[ -z ${AWS_ACCESS_KEY_ID} ]]; then
    echo "Provide env var for AWS_ACCESS_KEY_ID"
    exit 1
fi

if [[ -z ${AWS_SECRET_ACCESS_KEY} ]]; then
    echo "Provide env var for AWS_SECRET_ACCESS_KEY"
    exit 1
fi

if [[ -z ${AWS_DEFAULT_REGION} ]]; then
    echo "Provide env var for AWS_DEFAULT_REGION"
    exit 1
fi

if [[ -z ${KEYCLOAK_HOSTNAME} ]]; then
    echo "Provide env var for KEYCLOAK_HOSTNAME"
    exit 1
fi

if [[ -z ${KEYCLOAK_REALM} ]]; then
    echo "Provide env var for KEYCLOAK_REALM"
    exit 1
fi

if [[ -z ${AWS_ID_PRODIVER_NAME} ]]; then
    echo "Provide env var for AWS_ID_PRODIVER_NAME"
    exit 1
fi

if [[ -z ${AWS_IAM_ROLE_POLICY_ARN} ]]; then
    echo "Provide env var for AWS_IAM_ROLE_POLICY_ARN"
    exit 1
fi

if [[ -z ${AWS_IAM_ROLE_NAME} ]]; then
    echo "Provide env var for AWS_IAM_ROLE_NAME"
    exit 1
fi

if [[ -z ${AWS_ID_PRODIVER_NAME} ]]; then
    echo "Provide env var for AWS_ID_PRODIVER_NAME"
    exit 1
fi

if [[ -z ${AWS_IAM_ROLE_SESSION_DURATION} ]]; then
    echo "Provide env var for AWS_IAM_ROLE_SESSION_DURATION"
    exit 1
fi

if [[ -z ${KEYCLOAK_AWS_GROUP} ]]; then
    echo "Provide env var for KEYCLOAK_AWS_GROUP"
    exit 1
fi


echo "Configure AWS credentials..."
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}

echo "Create and configure AWS client, create users and groups as well in keycloak..."
clientOutput=$(python3.9 -W ignore create-client-aws.py)
print_failure "Failed to create client: ${clientOutput}"


echo "Export IDP SSO descriptor from keycloak"
curl -k -o SAML-Metadata-IDPSSODescriptor.xml "${KEYCLOAK_HOSTNAME}/auth/realms/${KEYCLOAK_REALM}/protocol/saml/descriptor"
print_failure "Failed to export IDP SSO descriptor"

echo "Creating the saml id provider..."
createSamlProviderOutput=$(aws iam create-saml-provider \
--saml-metadata-document file://SAML-Metadata-IDPSSODescriptor.xml \
--name ${AWS_ID_PRODIVER_NAME} --no-cli-pager 2>&1)
print_failure "${createSamlProviderOutput}"

samlProviderArn=$(echo $createSamlProviderOutput | jq -r '.SAMLProviderArn')
echo $samlProviderArn

echo "Create IAM Role and assigne policies..."
if [[ ! -f saml-assume-role-policy-doc.json ]]; then
    echo "saml-assume-role-policy-doc.json doesnt exist"
    exit 1
fi
cat saml-assume-role-policy-doc.json | jq ".Statement[0].Principal.Federated=\"${samlProviderArn}\"" > saml-assume-role-policy-doc-modified.json


createRoleOutput=$(aws iam create-role \
--role-name ${AWS_IAM_ROLE_NAME} \
--assume-role-policy-document file://saml-assume-role-policy-doc-modified.json --no-cli-pager 2>&1)
print_failure "Failed to create the iam role: ${createRoleOutput}"
roleArn=$(echo ${createRoleOutput} | jq -r '.Role.Arn')
echo $roleArn

echo "Update IAM role..."
aws iam attach-role-policy \
--role-name ${AWS_IAM_ROLE_NAME} \
--policy-arn ${AWS_IAM_ROLE_POLICY_ARN} --no-cli-pager
print_failure "Failed to update the iam role with policies"

echo "Finished AWS setup"
echo "Keycloak setup after AWS configuration..."

echo "Keycloak role mapping..."
roleName="${roleArn},${samlProviderArn}"
echo $roleName
export KEYCLOAK_AWS_MAPPING_ROLE_NAME=${roleName}
python3.9 update-keycloak-aws-configs.py