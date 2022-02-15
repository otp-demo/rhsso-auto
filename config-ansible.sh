#!/bin/bash
source ./utils.sh

# source .env
wait_for_preprocessing

echo "Getting Ansible Client ID"
export ANSIBLE_CLIENT_ID="$(oc get route controller -n ansible-automation-platform -o jsonpath='{.spec.host}')"
print_failure "Failed to get Ansible Client ID"

echo "Getting Ansible ACS URL"
export ANSIBLE_ACS_URL="https://$(oc get route controller -n ansible-automation-platform -o jsonpath='{.spec.host}')/sso/complete/saml/"
print_failure "Failed to get Ansible ACS URL"

echo "Getting Ansible Host URL"
export ANSIBLE_HOST_URL="https://$(oc get route controller -n ansible-automation-platform -o jsonpath='{.spec.host}')"
print_failure "Failed to get Ansible URL"

echo "Getting Ansible Redirect URI"
export ANSIBLE_REDIRECT_URI="https://$(oc get route controller -n ansible-automation-platform -o jsonpath='{.spec.host}')/sso/complete/saml/"
print_failure "Failed to get Ansible URL"

oc patch cm argocd-configs -n sso-integration -p "{\"data\": {\"ANSIBLE_CLIENT_ID\": \"${ANSIBLE_CLIENT_ID}\"}}"
print_failure "Failed to update Ansible Host URL"

oc patch cm argocd-configs -n sso-integration -p "{\"data\": {\"ANSIBLE_ACS_URL\": \"${ANSIBLE_ACS_URL}\"}}"
print_failure "Failed to update Ansible Host URL"

oc patch cm argocd-configs -n sso-integration -p "{\"data\": {\"ANSIBLE_HOST_URL\": \"${ANSIBLE_HOST_URL}\"}}"
print_failure "Failed to update Ansible Host URL"

oc patch cm argocd-configs -n sso-integration -p "{\"data\": {\"ANSIBLE_REDIRECT_URI\": \"${ANSIBLE_REDIRECT_URI}\"}}"
print_failure "Failed to update Ansible Host URL"

if [[ -z ${KEYCLOAK_HOSTNAME} ]] || [[ -z ${KEYCLOAK_REALM} ]]
then
    echo "Please provide KEYCLOAK_REALM and KEYCLOAK_HOSTNAME env vars"
    exit 1
fi

echo "Create and configure Ansible client..."
clientOutput=$(python3.9 -W ignore create-client-ansible.py)
print_failure "Failed to create client"

echo "Getting Ansible Client SAML URL"
export ANSIBLE_CLIENT_SAML_URL="https://$(oc get route controller -n ansible-automation-platform -o jsonpath='{.spec.host}')/sso/metadata/saml/"
print_failure "Failed to get Ansible Client SAML URL"

oc patch cm argocd-configs -n sso-integration -p "{\"data\": {\"ANSIBLE_CLIENT_SAML_URL\": \"${ANSIBLE_CLIENT_SAML_URL}\"}}"
print_failure "Failed to update Ansible Host URL"

echo "Create mappers for Ansible KeyCloak client..."
clientOutput=$(python3.9 -W ignore update-keycloak-ansible-configs.py)
print_failure "Failed to create mappers"