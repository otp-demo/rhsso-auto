#!/bin/bash
source ./utils.sh

# source .env
wait_for_preprocessing

echo "Getting ArgoCD URL"
export ARGO_ROOT_URL="https://$(oc get route openshift-gitops-cntk-server -n openshift-gitops -o jsonpath='{.spec.host}')"
print_failure "Failed to get Argocd URL"

oc patch cm argocd-configs -n sso-integration -p "{\"data\": {\"ARGO_ROOT_URL\": \"${ARGO_ROOT_URL}\"}}"
print_failure "Failed to update Argo URL"

if [[ -z ${KEYCLOAK_HOSTNAME} ]] || [[ -z ${KEYCLOAK_REALM} ]] || [[ -z ${ARGO_CLIENT_ID} ]]
then
    echo "Please provide KEYCLOAK_REALM and KEYCLOAK_HOSTNAME env vars"
    exit 1
fi

echo "Create and configure argocd client (idempotent), create users and groups as well in keycloak..."
clientOutput=$(python3.9 create-client.py)
print_failure "Failed to create client"

clientSecret=$(echo $clientOutput | sed 's/^.*Argo Client secret: \(.*\)$/\1/ig')
print_failure "Failed to filter out the created client secret"

encodedClientSecret=$(echo $clientSecret | base64)
echo $encodedClientSecret

NAMESPACE="openshift-gitops"
echo "Editing argocd-secret..."
oc patch secret argocd-secret -n ${NAMESPACE} -p "{\"data\": {\"oidc.keycloak.clientSecret\": \"${encodedClientSecret}\"}}"

echo "Editing configmap for ArgoCD CR..."
oidcConfigPath="name: Keycloak\nissuer: ${KEYCLOAK_HOSTNAME}/auth/realms/${KEYCLOAK_REALM}\nclientID: ${ARGO_CLIENT_ID}\nclientSecret: \$oidc.keycloak.clientSecret\nrequestedScopes: [\\\"openid\\\", \\\"profile\\\", \\\"email\\\", \\\"groups\\\"]\n"

oc get argocd openshift-gitops-cntk -o json -n openshift-gitops | jq ".spec.oidcConfig = \"${oidcConfigPath}\"" | oc apply -f -
print_failure "Failed to patch ArgoCD CR"

echo "Editing ArgoCD Policy"

oc patch cm argocd-rbac-cm -n ${NAMESPACE} -p "{\"data\": {\"policy.csv\": \"g, ArgoCDAdmins, role:admin\"}}"
print_failure "Failed to patch argocd policy"