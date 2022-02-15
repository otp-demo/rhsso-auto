from os import access
import requests
import simplejson as json
from utils import printResponse

def httpCommonHeaders(access_token):
    return {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json; charset=UTF-8"
    }
    
def raiseHttpExceptionMessage(response, extraMsg = ""):
    raise Exception("{}: {} - {}".format(response.status_code, response.text, extraMsg))

def getAccessToken(ssoUrl, realm, username, password, clientId, verifyTLS = True):
   headers = {
       "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
       "Cache-Control": "no-cache"
   }
   payload = "grant_type=password&username={}&password={}&client_id={}".format(
       username, password, clientId)
   tokenUrl = "{}/auth/realms/{}/protocol/openid-connect/token".format(
       ssoUrl, realm)
   
   response = requests.post(tokenUrl, data=payload, headers=headers, verify=verifyTLS)
   
   if response.status_code >= 200 and response.status_code < 300:
    identity_json = json.loads(response.text)
    access_token = identity_json['access_token'] 
    return access_token
   else:
    raiseHttpExceptionMessage(response)


def createRealm(ssoUrl, realm, accessToken, verify=True):
    response = requests.post("{}/auth/admin/realms".format(
                ssoUrl
                ), headers = httpCommonHeaders(accessToken),
                json = {
                    "enabled": True,
                    "id": realm,
                    "realm": realm
                }, verify = verify)
    if response.status_code == 201 or response.status_code == 409:
        print("Realm {} created".format(realm))
    else:
        raiseHttpExceptionMessage(response)

def createClient(ssoUrl, realm, accessToken, payload, tlsVerify):
    clientUrl = "{}/auth/admin/realms/{}/clients".format(
        ssoUrl, realm
    )
    response = requests.post(clientUrl, json=payload, headers=httpCommonHeaders(accessToken), verify=tlsVerify)
    if response.status_code == 201 or response.status_code == 409:
        print("Client created")
    else:
        raiseHttpExceptionMessage(response)
        
def getClientSecret(ssoUrl, realm, accessToken, clientId, verifyTLS = True):
    response = requests.get("{}/auth/admin/realms/{}/clients?clientId={}".format(
                ssoUrl, realm, clientId
            ), headers=httpCommonHeaders(accessToken), verify=verifyTLS)
    if response.status_code == 200:
       clientObjs = json.loads(response.text)
       if (len(clientObjs) > 0):
            clientUUID = clientObjs[0]["id"]
            response = requests.get("{}/auth/admin/realms/{}/clients/{}/client-secret".format(
                        ssoUrl, realm, clientUUID
                    ),headers = httpCommonHeaders(accessToken), verify=verifyTLS)
            if (response.status_code == 200):
                clientSecret = json.loads(response.text)["value"]
                return clientSecret
    raiseHttpExceptionMessage(response)

def getClientUUID(ssoUrl, realm, accessToken, clientId, verifyTLS = True):
    response = requests.get("{}/auth/admin/realms/{}/clients?clientId={}".format(
                ssoUrl, realm, clientId
            ), headers=httpCommonHeaders(accessToken), verify=verifyTLS)
    if response.status_code == 200:
       clientObjs = json.loads(response.text)
       if (len(clientObjs) > 0):
            clientUUID = clientObjs[0]["id"]
            return clientUUID
    raiseHttpExceptionMessage(response)
    
def createGroup(ssoUrl, realm, accessToken, groupName, tlsVerify):
    response = requests.post("{}/auth/admin/realms/{}/groups".format(
                            ssoUrl, realm), 
                            headers = httpCommonHeaders(accessToken), json = {
                                "name": groupName
                            }, verify=tlsVerify)
    if (response.status_code != 201) and (response.status_code != 409):
        raiseHttpExceptionMessage(response)
        
def getGroup(ssoUrl, realm, accessToken, groupName, tlsVerify):
   response = requests.get("{}/auth/admin/realms/{}/groups".format(ssoUrl, realm),
                           headers = httpCommonHeaders(accessToken), verify = tlsVerify)
   if response.status_code == 200:
       for group in json.loads(response.text):
           if group["name"] == groupName:
               return group
   raise Exception("Failed to get group info for {}".format(groupName))
        
def createUser(ssoUrl, realm, accessToken, email, 
               firstName, lastName, username, password,
                verifyTls = True, groupName = None):
    payload = {
                "attributes": {},
                "email": email,
                "emailVerified": True,
                "enabled": True,
                "firstName": firstName,
                "groups": [],
                "lastName": lastName,
                "username": username,
            }
    if groupName is not None:
        payload["groups"].append("/{}".format(groupName))
    response = requests.post("{}/auth/admin/realms/{}/users".format(
                            ssoUrl, realm), 
                            headers = httpCommonHeaders(accessToken), json = payload, verify=verifyTls)
    if (response.status_code == 201) or (response.status_code == 409):
        # Update the user with configured ARGO_ADMIN_PASSWORD, have to get users profile first...
        response = requests.get("{}/auth/admin/realms/{}/users?exact=true&&email={}".format(
            ssoUrl, realm, email), 
            headers = httpCommonHeaders(accessToken), verify=verifyTls)
        if response.status_code == 200:
            userId = json.loads(response.text)[0]["id"]
            response = requests.put("{}/auth/admin/realms/{}/users/{}/reset-password".format(
                ssoUrl, realm, userId), 
                headers = httpCommonHeaders(accessToken), json = {
                    "temporary": False,
                    "type": "password",
                    "value": password
                }, verify=verifyTls)
            if (response.status_code == 204):
                return True
    raise Exception("Failed to create the user: {}".format(username))

def joinGroup(ssoUrl, realm, accessToken, userEmail, groupUUID, verifyTls = True):
   response = requests.get("{}/auth/admin/realms/{}/users?email={}".format(ssoUrl, realm, userEmail),
                             headers = httpCommonHeaders(accessToken), verify = verifyTls)
   
   if response.status_code == 200:
       responseList = json.loads(response.text)
       if (len(responseList) == 0):
           raise Exception("User not found")
       userUUID = responseList[0]["id"]
       
       response = requests.put("{}/auth/admin/realms/{}/users/{}/groups/{}".format(
           ssoUrl, realm, userUUID, groupUUID
       ), headers = httpCommonHeaders(accessToken), json = {
           "realm": realm,
           "uesrId": userUUID,
           "groupId": groupUUID 
       }, verify = verifyTls)
       
       if (response.status_code == 204 or response.status_code == 409):
           print("User joined the group sucessfully.")
       else:
           raiseHttpExceptionMessage(response)
       return
   raiseHttpExceptionMessage(response)

def convertSaml2Json(ssoUrl, realm, accessToken, saml, verifyTls = False):
    response = requests.post("{}/auth/admin/realms/{}/client-description-converter".format(ssoUrl, realm),
                             headers = httpCommonHeaders(accessToken), data = saml, verify = verifyTls)
    if (response.status_code == 200):
        return json.loads(response.text)
    raiseHttpExceptionMessage(response)

def get(url, accessToken = None, verifyTls = True):
    if accessToken is None:
        response = requests.get(url, verify = verifyTls)
    else:
        response = requests.get(url, 
                 headers = httpCommonHeaders(accessToken), verify = verifyTls)
    if response.status_code == 200:
        return response.text
    else:
        raiseHttpExceptionMessage(response)


def createRole(ssoUrl, realm, accessToken, clientUUID, roleName, verifyTls = True):
    response = requests.post("{}/auth/admin/realms/{}/clients/{}/roles".format(ssoUrl, realm, clientUUID),
                             headers = httpCommonHeaders(accessToken), json = {
                                 "name": roleName,
                            }, verify=verifyTls)
    if response.status_code == 201 or response.status_code == 409:
            print("Role {} created".format(roleName))
    else:
        raiseHttpExceptionMessage(response)
        

def createClientMapping(ssoUrl, realm, accessToken, clientUUID, payload, verifyTls = True):
    response = requests.post("{}/auth/admin/realms/{}/clients/{}/protocol-mappers/models".format(ssoUrl, realm, clientUUID),
                             headers = httpCommonHeaders(accessToken), json = payload, verify=verifyTls)
    if response.status_code == 201 or response.status_code == 409:
            print("Mapper created")
    else:
        raiseHttpExceptionMessage(response)
        

def getClientScopeByName(ssoUrl, realm, accessToken, clientScopeName, verifyTls = True):
    response = requests.get("{}/auth/admin/realms/{}/client-scopes".format(ssoUrl, realm),
                            headers = httpCommonHeaders(accessToken), verify = verifyTls)
    if response.status_code == 200:
        clientScopes = json.loads(response.text)
        for clientScope in clientScopes:
            if (clientScope["name"] == clientScopeName):
                return clientScope
    else:
        raiseHttpExceptionMessage(response)

def deleteClientRoleFromClient(ssoUrl, realm, accessToken, clientUUID, clientScopeUUID, verifyTls = True):
    response = requests.delete("{}/auth/admin/realms/{}/clients/{}/default-client-scopes/{}".format(ssoUrl, realm, clientUUID, clientScopeUUID),
                            headers = httpCommonHeaders(accessToken), verify = verifyTls)
    if response.status_code != 204:
        raiseHttpExceptionMessage(response)
        
# updateJson
# {
#     "id": "7708f272-4cc8-474e-a7bf-9012228826c8",
#     "name": "role list",
#     "protocol": "saml",
#     "protocolMapper": "saml-role-list-mapper",
#     "consentRequired": false,
#     "config": {
#         "single": "true",
#         "attribute.nameformat": "Basic",
#         "attribute.name": "Role"
#     }
# }
def updateClientScopeMapper(ssoUrl, realm, accessToken, clientScope, targetProtocolMapperName, updateJson, verifyTls = True):
    targetProtocolMapperObj = None
    for protocolMapperObj in clientScope["protocolMappers"]:
        if (protocolMapperObj["protocolMapper"] == targetProtocolMapperName):
            targetProtocolMapperObj = protocolMapperObj
            break;
    
    updateJson["id"] = targetProtocolMapperObj["id"]
    response = requests.put("{}/auth/admin/realms/{}/client-scopes/{}/protocol-mappers/models/{}".format(ssoUrl, realm, clientScope["id"], targetProtocolMapperObj["id"]),
                            headers = httpCommonHeaders(accessToken), verify = verifyTls, json = updateJson)
    
    if response.status_code != 204:
         raiseHttpExceptionMessage(response)
   
def assignClientRole2Group(ssoUrl, realm, accessToken, groupUUID, clientUUID, mappingList, verifyTls = True):
    response = requests.post("{}/auth/admin/realms/{}/groups/{}/role-mappings/clients/{}".format(
        ssoUrl, realm, groupUUID, clientUUID
    ), headers = httpCommonHeaders(accessToken), verify = verifyTls, json = mappingList)
    
    if response.status_code == 204 or response.status_code == 409:
        print("Mapping succeeded")
        return
    raiseHttpExceptionMessage(response)
    
def getRealmComponent(ssoUrl, realm, accessToken, componentType, verifyTls = True):
    response = requests.get("{}/auth/admin/realms/{}/components?parent={}&type={}".format(
        ssoUrl, realm, realm, componentType
    ), headers = httpCommonHeaders(accessToken), verify = verifyTls)
    
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        raiseHttpExceptionMessage(response)
        
def deleteComponents(ssoUrl, realm, accessToken, componentList, verifyTls = True):
    if isinstance(componentList, list) == False:
        raise Exception("componentList is not a list")
    for component in componentList:
        print("Deleting component: {} ...".format(component["name"]))
        response = requests.delete("{}/auth/admin/realms/{}/components/{}".format(ssoUrl, realm, component["id"]),
                                   headers = httpCommonHeaders(accessToken), verify = verifyTls)
        if response.status_code != 204:
            raiseHttpExceptionMessage(response, json.dumps(component, indent = 4, sort_keys = True))
            

def createKeyComponent(ssoUrl, realm, accessToken, algorithm, providerId, cert, privateKey, verifyTls = True):
    json = {
        "config": {
            "active": ["true"],
            "algorithm": [algorithm],
            "certificate": [cert],
            "privateKey": [privateKey],
            "priority": ["0"],
            "enabled": ["true"]
        }, 
        "name": providerId,
        "parentId": realm,
        "providerId": providerId,
        "providerType": "org.keycloak.keys.KeyProvider"
    }
    
    response = requests.post("{}/auth/admin/realms/{}/components".format(ssoUrl, realm), 
                             headers = httpCommonHeaders(accessToken), verify = verifyTls, json = json)
    
    if response.status_code != 201 and response.status_code != 409:
        raiseHttpExceptionMessage(response)
    