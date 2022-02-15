import os
import sys
import requests
import simplejson as json
from utils import printResponse, enableHttpDebugLevel, formatedLogs
from httpUtils import get, getAccessToken, createRealm, convertSaml2Json,  httpCommonHeaders, getClientSecret, createClient, createUser
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
    clientSaml = get(os.environ["AWS_CLIENT_SAML_URL"])
    
    clientJson = convertSaml2Json(keycloakHost, keycloakRealm, access_token, clientSaml, TLS_VERIFY)
    clientJson["baseUrl"] = "/auth/realms/{}/protocol/saml/clients/amazon-aws".format(keycloakRealm)
    clientJson["attributes"]["saml_idp_initiated_sso_url_name"] = "amazon-aws"
    clientJson["fullScopeAllowed"] = False
    createClient(keycloakHost, keycloakRealm, access_token, clientJson, TLS_VERIFY)
    createUser(keycloakHost, keycloakRealm, access_token, 
               os.environ["ARGO_ADMIN_EMAIL"], os.environ["ARGO_ADMIN_FIRSTNAME"], os.environ["ARGO_ADMIN_LASTNAME"],
               os.environ["ARGO_ADMIN_USERNAME"], os.environ["ARGO_ADMIN_PASSWORD"], TLS_VERIFY
               )
except (KeyError): 
   print("Please set the environment variable")
   sys.exit(1)