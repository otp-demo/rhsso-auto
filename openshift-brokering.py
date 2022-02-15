import os
import sys
import requests
import simplejson as json
from utils import printResponse, enableHttpDebugLevel, formatedLogs
from httpUtils import httpCommonHeaders, getAccessToken, createRealm
from protocolMapper import ProtocolMapper
from protocols import Protocols

# from dotenv import load_dotenv
# load_dotenv()

try:
    if os.environ["HTTP_DEBUG"] == "true":
        enableHttpDebugLevel()

    username = os.environ["USER_NAME"]
    password = os.environ["PASSWORD"]
    adminClientId = os.environ["ADMIN_CLIENT_ID"]
    keycloakHost = os.environ["KEYCLOAK_HOSTNAME"]
    keycloakRealm = os.environ["KEYCLOAK_REALM"]

    # get token
    access_token = getAccessToken(keycloakHost, os.environ["MASTER_REALM"], username, password, adminClientId, False)
    
    # Create realm
    createRealm(keycloakHost, keycloakRealm, access_token, False)
    print("Set up Openshift identity provider on keycloak")
    response = requests.post("{}/auth/admin/realms/{}/identity-provider/instances".format(keycloakHost, keycloakRealm),
                            headers = httpCommonHeaders(access_token),
                            json = {
                                "addReadTokenRoleOnCreate": "",
                                "alias": "openshift-v4",
                                "authenticateByDefault": False,
                                "config": {
                                    "baseUrl": os.environ["OPENSHIFT_BROKER_API_SERVER"],
                                    "clientId": os.environ["OPENSHIFT_BROKER_CLIENT_ID"],
                                    "clientSecret": os.environ["OPENSHIFT_BROKER_CLIENT_SECRET"],
                                    "disableUserInfo": "",
                                    "hideOnLoginPage": "",
                                    "syncMode": "IMPORT",
                                    "useJwksUrl": "true",
                                },
                                "displayName": os.environ["OPENSHIFT_BROKER_DISPLAY_NAME"],
                                "enabled": True,
                                "firstBrokerLoginFlowAlias": "first broker login",
                                "linkOnly": "",
                                "postBrokerLoginFlowAlias": "",
                                "providerId": "openshift-v4",
                                "storeToken": "",
                                "trustEmail": "",
                            }, verify=False)

    if (response.status_code == 201 or response.status_code == 409):
        printResponse(response)
    
except (KeyError): 
   print("Please set the environment variable")
   sys.exit(1)