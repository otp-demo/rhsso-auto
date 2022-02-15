if [[ -z ${KEYCLOAK_HOSTNAME} ]]; then
    echo "Please set up KEYCLOAK_HOSTNAME"
    exit 1
fi

if [[ -z ${KEYCLOAK_REALM} ]]; then
    echo "Please set up KEYCLOAK_REALM"
    exit 1
fi

if [[ -z ${OPENSHIFT_BROKER_CLIENT_ID} ]]; then
    echo "Please set up OPENSHIFT_BROKER_CLIENT_ID"
    exit 1
fi

if [[ -z ${OPENSHIFT_BROKER_CLIENT_SECRET} ]]; then
    echo "Please set up OPENSHIFT_BROKER_CLIENT_SECRET"
    exit 1
fi

echo "Enable sso with OpenShift identity brokering"
python3.9 pre-processing.py

read -r -d '' oauthclient <<- EOM
kind: OAuthClient
apiVersion: oauth.openshift.io/v1
metadata:
 name: ${OPENSHIFT_BROKER_CLIENT_ID}
secret: "${OPENSHIFT_BROKER_CLIENT_SECRET}"
redirectURIs:
- "${KEYCLOAK_HOSTNAME}/auth/realms/${KEYCLOAK_REALM}/broker/openshift-v4/endpoint" 
grantMethod: prompt 
EOM

oc create -f <(echo "${oauthclient}") || true