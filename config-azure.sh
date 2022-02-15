#!/bin/bash
# source .env
source ./utils.sh

wait_for_preprocessing

function print_failure() 
{
    if [[ $? -ne 0 ]]; then
        echo $1
        exit 1
    fi
}

if [[ -z ${AZURE_CLIENT_ID} ]]; then
    echo "Provide env var for AZURE_CLIENT_ID"
    exit 1
fi

if [[ -z ${AZURE_X509_CERT} ]]; then
    echo "Provide env var for AZURE_X509_CERT"
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


if [[ -z ${KEYCLOAK_HOSTNAME} ]] || [[ -z ${KEYCLOAK_REALM} ]] || [[ -z ${AZURE_CLIENT_ID} ]]
then
    echo "Please provide KEYCLOAK_REALM and KEYCLOAK_HOSTNAME env vars"
    exit 1
fi

echo "Create and configure Azure client, create users and groups as well in keycloak..."
clientOutput=$(python3.9 create-client-azure.py)
print_failure "Failed to create client"
