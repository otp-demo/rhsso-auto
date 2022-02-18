import os
import sys
import requests
import simplejson as json
from utils import printResponse, enableHttpDebugLevel, formatedLogs
from httpUtils import httpCommonHeaders, getAccessToken, joinGroup, getGroup
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
    adminClientSecret = os.environ["ADMIN_CLIENT_SECRET"]
    keycloakHost = os.environ["KEYCLOAK_HOSTNAME"]
    keycloakRealm = os.environ["KEYCLOAK_REALM"]
    argoRoot = os.environ["ARGO_ROOT_URL"]

   # get token
    access_token = getAccessToken(keycloakHost, os.environ["MASTER_REALM"], username, password, adminClientId, TLS_VERIFY)

    # Create realm
    response = requests.post("{}/auth/admin/realms".format(
                keycloakHost, keycloakRealm
                ), headers = httpCommonHeaders(access_token),
                json = {
                    "enabled": True,
                    "id": keycloakRealm,
                    "realm": keycloakRealm
                }, verify=TLS_VERIFY)
    if response.status_code == 201 or response.status_code == 409:
        #   Create argo client on keycloak
        argoClientId = os.environ["ARGO_CLIENT_ID"]
        payload = {
            "attributes": {},
            "clientId": argoClientId,
            "enabled": True,
            "protocol": Protocols.OIDC.value,
            "redirectUris": [
                "{}/auth/callback".format(argoRoot)
            ],
            "rootUrl": argoRoot,
            "baseUrl": "/applications",
            "adminUrl": "{}/".format(argoRoot),
            "webOrigins": [argoRoot],
            "publicClient": False
        }
        clientUrl = "{}/auth/admin/realms/{}/clients".format(
            keycloakHost, keycloakRealm
        )
        response = requests.post(clientUrl, json=payload, headers=httpCommonHeaders(access_token), verify=TLS_VERIFY)
        if response.status_code == 201 or response.status_code == 409:
            # Get the client information to be used for configuration
            response = requests.get("{}/auth/admin/realms/{}/clients?clientId={}".format(
                keycloakHost, keycloakRealm, argoClientId
            ), headers=httpCommonHeaders(access_token), verify=TLS_VERIFY)

            if response.status_code == 200:
                clientObjs = json.loads(response.text)
                if (len(clientObjs) > 0):
                    argoClientUUID = clientObjs[0]["id"]
                    response = requests.get("{}/auth/admin/realms/{}/clients/{}/client-secret".format(
                        keycloakHost, keycloakRealm, argoClientUUID
                    ),headers = httpCommonHeaders(access_token), verify=TLS_VERIFY) 
                    if (response.status_code == 200):
                        argoClientSecret = json.loads(response.text)["value"]
                        formatedLogs("Create groups claim, and configured")
                    
                        # create groups scope
                        scopeName = "groups"
                        response = requests.post("{}/auth/admin/realms/{}/client-scopes".format(
                        keycloakHost, keycloakRealm, argoClientUUID
                        ),headers = httpCommonHeaders(access_token), json = {
                            "attributes": {
                                "display.on.consent.screen": "true",
                                "include.in.token.scope": "true"
                            },
                            "name": scopeName,
                            "protocol": Protocols.OIDC.value
                        }, verify=TLS_VERIFY)
                        if (response.status_code == 201) or (response.status_code == 409):
                            formatedLogs("Create protocol mappers for claim groups")
                            # Get the client-scope ID, no API provided for quering the ID with client scope name..., No resource limiting provided also, so gonna query for the whole list...
                            
                            response = requests.get("{}/auth/admin/realms/{}/client-scopes".format(
                                        keycloakHost, keycloakRealm
                                        ),headers = httpCommonHeaders(access_token), verify=TLS_VERIFY)
                            
                            if (response.status_code == 200):
                                clientScopes = json.loads(response.content)
                                clientScopeId = None
                                for clientScope in clientScopes:
                                    if (clientScope["name"] == "groups"):
                                        clientScopeId = clientScope["id"]
                                        break
                                if (clientScopeId is None):
                                    raise Exception("Groups scope not found")
                            
                            # Create groups mappers to be included in the claim   
                            response = requests.post("{}/auth/admin/realms/{}/client-scopes/{}/protocol-mappers/models".format(
                                keycloakHost, keycloakRealm, clientScopeId), 
                                headers = httpCommonHeaders(access_token), json = {
                                    "config": {
                                        "access.token.claim": "true",
                                        "claim.name": "groups",
                                        "full.path": "false",
                                        "id.token.claim": "true",
                                        "userinfo.token.claim": "true"
                                    },
                                    "name": scopeName,
                                    "protocol": Protocols.OIDC.value,
                                    "protocolMapper": ProtocolMapper.OIDC_GROUP_MEMBER_MAPPER.value
                                }, verify=TLS_VERIFY)
                            if (response.status_code == 201) or (response.status_code == 409):
                                # Assigned the client scope to the client created
                                response = requests.put("{}/auth/admin/realms/{}/clients/{}/default-client-scopes/{}".format(
                                keycloakHost, keycloakRealm, argoClientUUID, clientScopeId), 
                                headers = httpCommonHeaders(access_token), json = {}, verify=TLS_VERIFY)
                                if response.status_code == 204:
                                    formatedLogs("Create ArgoCDAdmins group, and join users")
                                    # Create group
                                    argoGroupName = os.environ["ARGO_GROUP_NAME"]
                                    response = requests.post("{}/auth/admin/realms/{}/groups".format(
                                                keycloakHost, keycloakRealm), 
                                                headers = httpCommonHeaders(access_token), json = {
                                                    "name": argoGroupName
                                                }, verify=TLS_VERIFY)
                                    if (response.status_code == 201) or (response.status_code == 409):
                                        # Create admin users, and join groups automatically
                                        response = requests.post("{}/auth/admin/realms/{}/users".format(
                                                keycloakHost, keycloakRealm), 
                                                headers = httpCommonHeaders(access_token), json = {
                                                    "attributes": {},
                                                    "email": os.environ["ARGO_ADMIN_EMAIL"],
                                                    "emailVerified": True,
                                                    "enabled": True,
                                                    "firstName": os.environ["ARGO_ADMIN_FIRSTNAME"],
                                                    "groups": ["/{}".format(argoGroupName)],
                                                    "lastName": os.environ["ARGO_ADMIN_LASTNAME"],
                                                    "username": os.environ["ARGO_ADMIN_USERNAME"],
                                                }, verify=TLS_VERIFY)
                                        
                                        if (response.status_code == 201) or (response.status_code == 409):
                                            # Update the user with configured ARGO_ADMIN_PASSWORD, have to get users profile first...
                                            response = requests.get("{}/auth/admin/realms/{}/users?exact=true&&email={}".format(
                                                keycloakHost, keycloakRealm, os.environ["ARGO_ADMIN_EMAIL"]), 
                                                headers = httpCommonHeaders(access_token), verify=TLS_VERIFY)

                                            if response.status_code == 200:
                                                userId = json.loads(response.text)[0]["id"]
                                                response = requests.put("{}/auth/admin/realms/{}/users/{}/reset-password".format(
                                                    keycloakHost, keycloakRealm, userId), 
                                                    headers = httpCommonHeaders(access_token), json = {
                                                        "temporary": False,
                                                        "type": "password",
                                                        "value": os.environ["ARGO_ADMIN_PASSWORD"]
                                                    }, verify=TLS_VERIFY)
                                                if (response.status_code == 204):
                                                    groupUUID = getGroup(keycloakHost, keycloakRealm, access_token, argoGroupName, TLS_VERIFY)['id']
                                                    joinGroup(keycloakHost, keycloakRealm, access_token, os.environ["ARGO_ADMIN_EMAIL"], groupUUID, TLS_VERIFY)
                                                    print("Client {} created, and configured for argocd\nArgo Client secret: {}".format(argoClientId, argoClientSecret))
        else:
            raise Exception("No client found")  
except (KeyError): 
   print("Please set the environment variable")
   sys.exit(1)