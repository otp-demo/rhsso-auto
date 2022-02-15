import os
import sys
import requests
import simplejson as json
import xml.etree.ElementTree as ET

from utils import printResponse, enableHttpDebugLevel, formatedLogs
from httpUtils import get, createRole, getAccessToken, getClientUUID, createClientMapping, createGroup, getGroup, assignClientRole2Group, createUser, joinGroup, getClientScopeByName, deleteClientRoleFromClient
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
    
    access_token = getAccessToken(keycloakHost, os.environ["MASTER_REALM"], username, password, adminClientId, TLS_VERIFY)
    
    clientSaml = get(os.environ["AWS_CLIENT_SAML_URL"], access_token, TLS_VERIFY)
    samlTree = ET.fromstring(clientSaml)
    clientId = samlTree.attrib["entityID"]
    clientUUID = getClientUUID(keycloakHost, keycloakRealm, access_token, clientId, TLS_VERIFY)
    
    print("Create roles...")
    createRole(keycloakHost, keycloakRealm, access_token, clientUUID, os.environ["KEYCLOAK_AWS_MAPPING_ROLE_NAME"], TLS_VERIFY)
    
    print("-----------Create mappers-----------")
    print("Create mappers session role...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "attribute.name": "https://aws.amazon.com/SAML/Attributes/Role",
            "attribute.nameformat": "Basic",
            "friendly.name": "Session Role",
            "single": "true",
        },
        "name": "Session Role",
        "protocol": "saml",
        "protocolMapper": "saml-role-list-mapper",
    }, TLS_VERIFY)
    
    print("Create mappers user property...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "attribute.name": "https://aws.amazon.com/SAML/Attributes/RoleSessionName",
            "attribute.nameformat": "Basic",
            "friendly.name": "Session Name",
            "user.attribute": "username",
        },
        "name": "Session Name",
        "protocol": "saml",
        "protocolMapper": "saml-user-property-mapper",
    }, TLS_VERIFY)
    
    print("Create mappers user property...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "attribute.name": "https://aws.amazon.com/SAML/Attributes/RoleSessionName",
            "attribute.nameformat": "Basic",
            "friendly.name": "Session Name",
            "user.attribute": "username",
        },
        "name": "Session Name",
        "protocol": "saml",
        "protocolMapper": "saml-user-property-mapper",
    }, TLS_VERIFY)
    
    print("Create mappers session duration...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "attribute.name": "https://aws.amazon.com/SAML/Attributes/SessionDuration",
            "attribute.nameformat": "Basic",
            "attribute.value": os.environ["AWS_IAM_ROLE_SESSION_DURATION"],
            "friendly.name": "Session Duration",
        },
        "name": "Session Duration",
        "protocol": "saml",
        "protocolMapper": "saml-hardcode-attribute-mapper",
    }, TLS_VERIFY) 
    
    print("Create mappers session duration...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "attribute.name": "https://aws.amazon.com/SAML/Attributes/SessionDuration",
            "attribute.nameformat": "Basic",
            "attribute.value": os.environ["AWS_IAM_ROLE_SESSION_DURATION"],
            "friendly.name": "Session Duration",
        },
        "name": "Session Duration",
        "protocol": "saml",
        "protocolMapper": "saml-hardcode-attribute-mapper",
    }, TLS_VERIFY)
    
    createGroup(keycloakHost, keycloakRealm, access_token, os.environ["KEYCLOAK_AWS_GROUP"], TLS_VERIFY)
    groupUUID = getGroup(keycloakHost, keycloakRealm, access_token, os.environ["KEYCLOAK_AWS_GROUP"], TLS_VERIFY)['id']
    
    print("Getting the role mapping id for the client...")
    roleMappingList= json.loads(get("{}/auth/admin/realms/{}/groups/{}/role-mappings/clients/{}/available".format(
        keycloakHost, keycloakRealm, groupUUID, clientUUID
    ), access_token, TLS_VERIFY))
    
    if (len(roleMappingList) > 0):
        print("Assign the role mapping id for the client...")
        roleMapping = None
        for roleMappingObj in roleMappingList:
            if (roleMappingObj["name"] == os.environ["KEYCLOAK_AWS_MAPPING_ROLE_NAME"]):
                roleMapping = roleMappingObj
                break
        if roleMapping is None:
            raise Exception("Not role mapping found")
        assignClientRole2Group(keycloakHost, keycloakRealm, access_token, groupUUID, clientUUID, [roleMapping], TLS_VERIFY)
    createUser(keycloakHost, keycloakRealm, access_token,
            os.environ["ARGO_ADMIN_EMAIL"], os.environ["ARGO_ADMIN_FIRSTNAME"], os.environ["ARGO_ADMIN_LASTNAME"],
            os.environ["ARGO_ADMIN_USERNAME"], os.environ["ARGO_ADMIN_PASSWORD"], TLS_VERIFY)
    joinGroup(keycloakHost, keycloakRealm, access_token, os.environ["ARGO_ADMIN_EMAIL"], groupUUID, TLS_VERIFY)
    
    print("Remove default role list client scope from the client...")
    clientScopeObj = getClientScopeByName(keycloakHost, keycloakRealm, access_token, "role_list", TLS_VERIFY)
    deleteClientRoleFromClient(keycloakHost, keycloakRealm, access_token, clientUUID, clientScopeObj["id"], TLS_VERIFY)
except KeyError as e: 
    print("Please set the environment variable: {}".format(str(e)))
    sys.exit(1)