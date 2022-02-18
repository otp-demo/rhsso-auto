#!/bin/bash
source .env

KEYCLOAK_ORIGINAL_HOSTNAME="https://$(oc get route keycloak -n sso -o jsonpath='{.spec.host}')"
PASSWORD=$(oc get secret credential-rhsso -n sso -o jsonpath='{.data.ADMIN_PASSWORD}' | base64 -d)
USERNAME=$(oc get secret credential-rhsso -n sso -o jsonpath='{.data.ADMIN_USERNAME}' | base64 -d)
KEYCLOAK_HOSTNAME="https://$(oc get route keycloak-custom-domain -n sso -o jsonpath='{.spec.host}')"

if [[ $? -ne 0 ]]; then
    KEYCLOAK_HOSTNAME=${KEYCLOAK_ORIGINAL_HOSTNAME}
fi

echo "Adding the argocd-configs to cluster..."
oc apply -f ../k8s/sso-configs.yaml

oc patch cm argocd-configs -n sso-integration \
-p "{\"data\": {\"PASSWORD\": \"${PASSWORD}\", \"USER_NAME\": \"${USERNAME}\", \"KEYCLOAK_HOSTNAME\": \"${KEYCLOAK_HOSTNAME}\"}}"

if [[ -n ${KEYCLOAK_ORIGINAL_HOSTNAME} ]]; then
   echo "KEYCLOAK_ORIGINAL_HOSTNAME: ${KEYCLOAK_ORIGINAL_HOSTNAME} found."
   oc get cm argocd-configs -n sso-integration -o json |\
   jq ".data.KEYCLOAK_ORIGINAL_HOSTNAME=\"${KEYCLOAK_ORIGINAL_HOSTNAME}\"" |\
   oc apply -f -
fi