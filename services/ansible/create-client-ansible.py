import os
import sys
import simplejson as json
from utils import printResponse, enableHttpDebugLevel, formatedLogs
from httpUtils import getAccessToken, createRealm, createClient, getRealmComponent, deleteComponents, createKeyComponent
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
    #   Create Ansible client on keycloak
    ANSIBLE_CLIENT_ID = os.environ["ANSIBLE_CLIENT_ID"]
    ANSIBLE_X509_CERT = os.environ["ANSIBLE_X509_CERT"]
    ANSIBLE_ACS_URL = os.environ["ANSIBLE_ACS_URL"]
    ANSIBLE_HOST_URL = os.environ["ANSIBLE_HOST_URL"]
    ANSIBLE_REDIRECT_URI = os.environ["ANSIBLE_REDIRECT_URI"]
    
    payload = {
        "attributes": {
            "saml.force.post.binding": "true",
            "saml.multivalued.roles": "false",
            "oauth2.device.authorization.grant.enabled": "false",
            "backchannel.logout.revoke.offline.tokens": "false",
            "saml.server.signature.keyinfo.ext": "false",
            "use.refresh.tokens": "true",
            "saml.signing.certificate": ANSIBLE_X509_CERT,
            "oidc.ciba.grant.enabled": "false",
            "backchannel.logout.session.required": "false",
            "saml.signature.algorithm": "RSA_SHA256",
            "client_credentials.use_refresh_token": "false",
            "saml.client.signature": "false",
            "require.pushed.authorization.requests": "false",
            "saml.assertion.signature": "true",
            "id.token.as.detached.signature": "false",
            "saml.encrypt": "false",
            "saml_assertion_consumer_url_post": ANSIBLE_ACS_URL,
            "saml.server.signature": "true",
            "saml_idp_initiated_sso_url_name": ANSIBLE_CLIENT_ID,
            "exclude.session.state.from.auth.response": "false",
            "saml.artifact.binding": "false",
            "saml_force_name_id_format": "false",
            "tls.client.certificate.bound.access.tokens": "false",
            "saml.authnstatement": "true",
            "display.on.consent.screen": "false",
            "saml_name_id_format": "username",
            "saml_signature_canonicalization_method": "http://www.w3.org/2001/10/xml-exc-c14n#",
            "saml.onetimeuse.condition": "false"
        },
        "clientId": ANSIBLE_CLIENT_ID,
        "name": "Ansible Tower",
        "enabled": True,
        "protocol": Protocols.SAML.value,
        "webOrigins": [
            ANSIBLE_HOST_URL
        ],
        "redirectUris": [
            ANSIBLE_REDIRECT_URI
        ],
        "rootUrl": ANSIBLE_HOST_URL,
        "publicClient": False,
        "directAccessGrantsEnabled": False,
        "frontchannelLogout": True
    }
    createClient(keycloakHost, keycloakRealm, access_token, payload, TLS_VERIFY)
    
    print("Clear all keys and certificates...")
    realmComponents = getRealmComponent(keycloakHost, keycloakRealm, access_token, "org.keycloak.keys.KeyProvider", TLS_VERIFY)
    deleteComponents(keycloakHost, keycloakRealm, access_token, realmComponents, TLS_VERIFY)
    createKeyComponent(keycloakHost, keycloakRealm, access_token, "RS256", "rsa", 
                       os.environ["ANSIBLE_KEY_CERT"], os.environ["ANSIBLE_KEY_PRIVATE_KEY"], TLS_VERIFY)
except KeyError as e: 
   print("Please set the environment variable: {}".format(e.message))
   sys.exit(1)