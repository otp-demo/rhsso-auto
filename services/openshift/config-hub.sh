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

if [[ -z ${CLUSTER_CLIENT_ID} ]]; then
    echo "Provide env var for CLUSTER_CLIENT_ID"
    exit 1
fi

if [[ -z ${OPENSHIFT_OAUTH_NAME} ]]; then
    echo "Provide env var for OPENSHIFT_OAUTH_NAME"
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

if [[ -z ${ARGO_ADMIN_USERNAME} ]]; then
    echo "Provide env var for ARGO_ADMIN_USERNAME"
    exit 1
fi

CA_CERT_BUNDLE=$(oc get secret sso-configs -n sso-integration -o jsonpath='{.data.CA_CERT_BUNDLE}' | base64 -d)

if [[ -n ${IS_MANAGED_CLUSTER} ]]; then
  export CLUSTER_SECRET_NAME=$(oc get clusterdeployment ${CLUSTER_CLIENT_ID} -n ${CLUSTER_CLIENT_ID} -o jsonpath='{.spec.clusterMetadata.adminPasswordSecretRef.name}')
  export KUBE_ADMIN_SECRET=$(oc get secret ${CLUSTER_SECRET_NAME} -n ${CLUSTER_CLIENT_ID} -o jsonpath='{.data.password}' | base64 -d)
  export KUBE_ADMIN_USERNAME=$(oc get secret ${CLUSTER_SECRET_NAME} -n ${CLUSTER_CLIENT_ID} -o jsonpath='{.data.username}' | base64 -d)
  export CLUSTER_API_URL=$(oc get clusterdeployment ${CLUSTER_CLIENT_ID} -n ${CLUSTER_CLIENT_ID} -o jsonpath='{.status.apiURL}')
  if [[ -z ${KUBE_ADMIN_SECRET} ]]; then
    echo "Failed to get the admin creds"
    exit 1
  fi
  if [[ -z ${CLUSTER_API_URL} ]]; then
    echo "Failed to get the CLUSTER_API_URL"
    exit 1
  fi

  echo "Logging into ${CLUSTER_API_URL}"
  # TODO: removed insecure tls verity skip in the future once the manged clusters could be automatically provided with certs
  oc login --insecure-skip-tls-verify=true -u ${KUBE_ADMIN_USERNAME} -p ${KUBE_ADMIN_SECRET} ${CLUSTER_API_URL}
  print_failure "Failed to login the managed cluster"
fi

echo "Getting oauth route"
export CLUSTER_OAUTH_URL="https://$(oc get route oauth-openshift -n openshift-authentication -o jsonpath='{.spec.host}')"


echo "Creating the client on Keycloak..."
createClientOutput=$(python3.9 create-client-openshift.py 2>&1)
print_failure ${createClientOutput}

clientSecret=$(echo $createClientOutput | sed 's/^.*clientSecret: \(.*\)$/\1/ig' 2>&1)
print_failure "Failed to filter out the created client secret"
encodedClientSecret=$(echo ${clientSecret} | base64)

echo "Creating the secret to be referened in OAuth CR"
oc delete secret ${OPENSHIFT_OAUTH_NAME}-client-secret -n openshift-config
oc create secret generic ${OPENSHIFT_OAUTH_NAME}-client-secret --from-literal=clientSecret=${clientSecret} -n openshift-config

echo "Creating configmap for ca certificates in case the keycloak server is using a self-signed or intermediate certificates..."
if [[ -n ${CA_CERT_BUNDLE} ]]; then
  echo "Create from configmap"
  oc create configmap ca-config-map --from-literal=ca.crt="${CA_CERT_BUNDLE}" -n openshift-config
fi



echo "Removing existing user if existing"

echo "Configured OAuth CR..."

read -r -d '' oauthCR <<- EOM
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  annotations:
    include.release.openshift.io/ibm-cloud-managed: "true"
    include.release.openshift.io/self-managed-high-availability: "true"
    include.release.openshift.io/single-node-developer: "true"
    release.openshift.io/create-only: "true"
  name: cluster
spec:
  identityProviders:
  - mappingMethod: claim
    name: ${OPENSHIFT_OAUTH_NAME}
    openID:
      claims:
        email:
        - email
        name:
        - name
        preferredUsername:
        - preferred_username
      clientID: ${CLUSTER_CLIENT_ID}
      clientSecret:
        name: ${OPENSHIFT_OAUTH_NAME}-client-secret
      issuer: ${KEYCLOAK_HOSTNAME}/auth/realms/${KEYCLOAK_REALM}
    type: OpenID
EOM

if [[ -n ${CA_CERT_BUNDLE} ]]; then
read -r -d '' oauthCR <<- EOM
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  annotations:
    include.release.openshift.io/ibm-cloud-managed: "true"
    include.release.openshift.io/self-managed-high-availability: "true"
    include.release.openshift.io/single-node-developer: "true"
    release.openshift.io/create-only: "true"
  name: cluster
spec:
  identityProviders:
  - mappingMethod: claim
    name: ${OPENSHIFT_OAUTH_NAME}
    openID:
      ca:
        name: ca-config-map
      claims:
        email:
        - email
        name:
        - name
        preferredUsername:
        - preferred_username
      clientID: ${CLUSTER_CLIENT_ID}
      clientSecret:
        name: ${OPENSHIFT_OAUTH_NAME}-client-secret
      issuer: ${KEYCLOAK_HOSTNAME}/auth/realms/${KEYCLOAK_REALM}
    type: OpenID
EOM
fi

oc apply -f <(echo "${oauthCR}")
print_failure "Failed to config OAuth CR"

echo "Removed old settings and also check to assigne cluster admin role to the user..."
# Create cluster role binding for admin users...
if [[ ${CLUSTER_IS_ADMIN} -eq "true" ]]; then
    echo "Assign cluster-admin role to admin user"
    oc create clusterrolebinding admin-oauth-binding --clusterrole="cluster-admin" --user=admin
fi

#  Check if the user exists. If so, remove users and releavnt identity to avoid potential errors
oc delete user ${ARGO_ADMIN_USERNAME}
identityName=$(oc get identity --field-selector providerName=${OPENSHIFT_OAUTH_NAME} -o name)

if [[ -z ${identityName} ]]; then
    echo "identityName doesnt exist, exit successfully"
    exit 0
fi
oc delete ${identityName}