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
    #   Create Azure client on keycloak
    azureclientId = os.environ["AZURE_CLIENT_ID"]
    AZURE_X509_CERT = os.environ["AZURE_X509_CERT"]
    
    payload = {
        "attributes": {
            "saml.force.post.binding": "true",
            "saml.multivalued.roles": "false",
            "oauth2.device.authorization.grant.enabled": "false",
            "backchannel.logout.revoke.offline.tokens": "false",
            "saml.server.signature.keyinfo.ext": "false",
            "use.refresh.tokens": "true",
            "saml.signing.certificate": AZURE_X509_CERT,
            "oidc.ciba.grant.enabled": "false",
            "backchannel.logout.session.required": "false",
            "client_credentials.use_refresh_token": "false",
            "saml.signature.algorithm": "RSA_SHA1",
            "require.pushed.authorization.requests": "false",
            "saml.client.signature": "false",
            "id.token.as.detached.signature": "false",
            "saml.assertion.signature": "true",
            "saml_single_logout_service_url_post": "https://login.microsoftonline.com/login.srf",
            "saml.encrypt": "false",
            "saml_assertion_consumer_url_post": "https://login.microsoftonline.com/login.srf",
            "saml.server.signature": "true",
            "exclude.session.state.from.auth.response": "false",
            "saml.artifact.binding": "false",
            "saml_force_name_id_format": "false",
            "tls.client.certificate.bound.access.tokens": "false",
            "saml.authnstatement": "true",
            "display.on.consent.screen": "false",
            "saml_name_id_format": "email",
            "saml.onetimeuse.condition": "false",
            "saml_signature_canonicalization_method": "http://www.w3.org/2001/10/xml-exc-c14n#"
        },
        "clientId": azureclientId,
        "enabled": True,
        "protocol": Protocols.SAML.value,
        "webOrigins": [
        "https://login.microsoftonline.com"
        ],
        "redirectUris": [
            "https://login.microsoftonline.com/login.srf"
        ],
        "publicClient": False,
        "directAccessGrantsEnabled": False,
        "frontchannelLogout": True
    }
    createClient(keycloakHost, keycloakRealm, access_token, payload, TLS_VERIFY)

    createUser(keycloakHost, keycloakRealm, access_token, 
               os.environ["ARGO_ADMIN_EMAIL"], os.environ["ARGO_ADMIN_FIRSTNAME"], os.environ["ARGO_ADMIN_LASTNAME"],
               os.environ["ARGO_ADMIN_USERNAME"], os.environ["ARGO_ADMIN_PASSWORD"], TLS_VERIFY
               )
               
except KeyError as e: 
   print("Please set the environment variable: {}".format(e.message))
   sys.exit(1)