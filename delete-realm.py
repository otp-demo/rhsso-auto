import os
import requests
import simplejson as json
from utils import printResponse, enableHttpDebugLevel, formatedLogs
from httpUtils import httpCommonHeaders, getAccessToken

from dotenv import load_dotenv
load_dotenv()

try:
    if os.environ["HTTP_DEBUG"] == "true":
        enableHttpDebugLevel()
    username = os.environ["USER_NAME"]
    password = os.environ["PASSWORD"]
    adminClientId = os.environ["ADMIN_CLIENT_ID"]
    adminClientSecret = os.environ["ADMIN_CLIENT_SECRET"]
    keycloakHost = os.environ["KEYCLOAK_HOSTNAME"]
    # keycloakRealm = os.environ["KEYCLOAK_REALM"]
    keycloakRealm = "test"
    
    access_token = getAccessToken(keycloakHost, os.environ["MASTER_REALM"], username, password, adminClientId, False)
    
    response = requests.delete("{}/auth/admin/realms/{}".format(
        keycloakHost, keycloakRealm), headers = httpCommonHeaders(access_token), verify = False)
    
    printResponse(response)
except (KeyError): 
   print("Please set the environment variable")
   sys.exit(1)
