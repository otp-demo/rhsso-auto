import os
import sys
import simplejson as json
from utils import printResponse, enableHttpDebugLevel, formatedLogs
from httpUtils import getAccessToken, createRealm, getClientSecret, createClient, createUser
from protocolMapper import ProtocolMapper
from protocols import Protocols

# from dotenv import load_dotenv
# load_dotenv()

try:
    if os.environ["HTTP_DEBUG"] == "true":
        enableHttpDebugLevel()

    TLS_VERIFY = True if os.environ["TLS_VERIFY"] == "true" else False

    username = os.environ["USER_NAME"]
    password = os.environ["PASSWORD"]
    adminClientId = os.environ["ADMIN_CLIENT_ID"]
    keycloakHost = os.environ["KEYCLOAK_HOSTNAME"]
    keycloakRealm = os.environ["KEYCLOAK_REALM"]

   # get token
    access_token = getAccessToken(keycloakHost, os.environ["MASTER_REALM"], username, password, adminClientId, TLS_VERIFY)
    # Create realm
    createRealm(keycloakHost, keycloakRealm, access_token, TLS_VERIFY)
    #   Create openshift client on keycloak
    clientId = os.environ["CLUSTER_CLIENT_ID"]
    hubOauthRoot = os.environ["CLUSTER_OAUTH_URL"]
    
    payload = {
        "attributes": {},
        "clientId": clientId,
        "enabled": True,
        "protocol": Protocols.OIDC.value,
        "redirectUris": [
            "{}/oauth2callback/{}".format(hubOauthRoot, os.environ["OPENSHIFT_OAUTH_NAME"])
        ],
        "publicClient": False,
        "directAccessGrantsEnabled": False
    }
    createClient(keycloakHost, keycloakRealm, access_token, payload, TLS_VERIFY)
    clientSecret = getClientSecret(keycloakHost, keycloakRealm, access_token, clientId, TLS_VERIFY)
    
    createUser(keycloakHost, keycloakRealm, access_token, 
               os.environ["ARGO_ADMIN_EMAIL"], os.environ["ARGO_ADMIN_FIRSTNAME"], os.environ["ARGO_ADMIN_LASTNAME"],
               os.environ["ARGO_ADMIN_USERNAME"], os.environ["ARGO_ADMIN_PASSWORD"], TLS_VERIFY
               )
    print("clientSecret: {}".format(clientSecret))
except (KeyError): 
   print("Please set the environment variable")
   sys.exit(1)