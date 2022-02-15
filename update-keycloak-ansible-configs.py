import os
import sys
import requests
import simplejson as json
import xml.etree.ElementTree as ET

from utils import printResponse, enableHttpDebugLevel, formatedLogs
from httpUtils import get, getAccessToken, getClientUUID, createClientMapping, getClientScopeByName, updateClientScopeMapper 
from protocolMapper import ProtocolMapper
from protocols import Protocols

from dotenv import load_dotenv
load_dotenv()

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
    
    clientSaml = get(os.environ["ANSIBLE_CLIENT_SAML_URL"], access_token, TLS_VERIFY)
    samlTree = ET.fromstring(clientSaml)
    clientId = samlTree.attrib["entityID"]
    clientUUID = getClientUUID(keycloakHost, keycloakRealm, access_token, clientId, TLS_VERIFY)
    
    print("-----------Create mappers-----------")
    print("Create mappers user_permanent_id...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "attribute.nameformat": "Basic",
            "user.attribute": "uid",
            "friendly.name": "name_id",
            "attribute.name": "name_id",
        },
        "name": "user_permanent_id",
        "protocol": "saml",
        "protocolMapper": "saml-user-attribute-mapper",
        # "consentRequired": false,
    }, TLS_VERIFY)
    
    print("Create mappers first_name...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "attribute.nameformat": "Basic",
            "user.attribute": "firstName",
            "friendly.name": "First Name",
            "attribute.name": "first_name",
        },
        "name": "first_name",
        "protocol": "saml",
        "protocolMapper": "saml-user-property-mapper",
        # "consentRequired": false,
    }, TLS_VERIFY)

    print("Create mappers email...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "attribute.nameformat": "Basic",
            "user.attribute": "email",
            "friendly.name": "Email",
            "attribute.name": "email",
        },
        "name": "email",
        "protocol": "saml",
        "protocolMapper": "saml-user-property-mapper",
        # "consentRequired": false,
    }, TLS_VERIFY)

    print("Create mappers user_name...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "attribute.nameformat": "Basic",
            "user.attribute": "username",
            "friendly.name": "User Name",
            "attribute.name": "username",
        },
        "name": "user_name",
        "protocol": "saml",
        "protocolMapper": "saml-user-property-mapper",
        # "consentRequired": false,
    }, TLS_VERIFY)

    print("Create mappers groups...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "single": "true",
            "attribute.nameformat": "Basic",
            "full.path": "true",
            "friendly.name": "Group list",
            "attribute.name": "member",
        },
        "name": "groups",
        "protocol": "saml",
        "protocolMapper": "saml-group-membership-mapper",
        # "consentRequired": false,
    }, TLS_VERIFY)

    print("Create mappers last_name...")
    createClientMapping(keycloakHost, keycloakRealm, access_token, clientUUID, {
        "config": {
            "attribute.name": "member",
            "attribute.nameformat": "Basic",
            "user.attribute": "lastName",
            "friendly.name": "Last Name",
            "attribute.name": "last_name",
        },
        "name": "last_name",
        "protocol": "saml",
        "protocolMapper": "saml-user-property-mapper",
        # "consentRequired": false,
    }, TLS_VERIFY)

    print("Last but not least, enable single role attribute...")
    clientScopeObj = getClientScopeByName(keycloakHost, keycloakRealm, access_token, "role_list", TLS_VERIFY)
    print(clientScopeObj)
    updateClientScopeMapper(keycloakHost, keycloakRealm, access_token, clientScopeObj, "saml-role-list-mapper", {
        "name": "role list",
        "protocol": "saml",
        "protocolMapper": "saml-role-list-mapper",
        "consentRequired": False,
        "config": {
            "single": "true",
            "attribute.nameformat": "Basic",
            "attribute.name": "Role"
        }
    }, TLS_VERIFY)
except KeyError as e: 
    print("Please set the environment variable: {}".format(str(e)))
    sys.exit(1)