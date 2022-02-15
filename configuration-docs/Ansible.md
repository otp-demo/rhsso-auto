# RH-SSO integration with Ansible

## Introduction
The purpose of this readme is to provide step by step guide to integrate RH-SSO with Ansible Controller. After your RH-SSO instance is deployed you can use below guide to implement SAML SSO between RH-SSO (IdP) and Ansible (SP). You can automate the deployment of realm client for Ansible via Jobs and ArgoCD but SAML configuration on Ansible Controller must be done manually by Ansible Administrator.

## Prerequisites 
- Working RH-SSO instance
- Working Ansible Controller instance
- Administrator access for Ansible and RH-SSO

## Configuration
* **Step 1: Fetch certificates and keys**
  * If Ansible Client for RHSSO was deployed via GitOps and Argo CD, you can execute following commands to fetch values for `X509_CERT` and `KEY_CERT`
  ```
  oc get secret sso-configs -n sso-integration -o jsonpath="{.data.ANSIBLE_X509_CERT}" | base64 -d
  oc get secret sso-configs -n sso-integration -o jsonpath="{.data.ANSIBLE_KEY_CERT}" | base64 -d
  ```

* **Step 2: Ensure that client for Ansible Controller exist on RH-SSO realm**
  * Using GitOps pattern a client should automatically get deployed onto your RH-SSO instance for Ansible
  * Logon to your RH-SSO instance and check following:
    * Under your realm, check if a client exist starting with `controller-ansible-automation-platform`
    * Under Realm Settings --> Keys, check if default keys such as `aes-generated`, `hmac-generated`, `rsa-generated`, `rsa-enc-generated` are NOT present and keys `rsa` and `fallback-HS256` are present.
    * If you are unable to see the client or default keys are not removed, check if Job has run successfully on your cluster
    
* **Step 3: Login as admin user on Ansible Controller**
  * You can use `oc get secret controller-admin-password -n ansible-automation-platform -o jsonpath="{.data.password}" | base64 -d` to retrieve login credentials for administrator. Open Ansible Controller webpage and sign in using Administrator credentials

* **Step 4: Configure SAML settings on Ansible Controller**
  * After signing in as Administrator, click on Settings --> SAML Settings
  * Scroll at the bottom of the page and click on Edit to modify SAML Settings
  * Configure following:
    * SAML Service Provider Entity ID: host url of Ansible Controller instance: eg. `controller-ansible-automation-platform.apps.hub.mcm-aiops-gitops.acme.com`
    * Automatically Create Organizations and Teams on SAML Login: ON
    * SAML Service Provider Public Certificate: value of your `X509_CERT`
    * SAML Service Provider Private Key: value of your `KEY_CERT`
    * SAML Service Provider Organization Info:
      ```
      {
        "en-US": {
          "name": "RHSSO",
          "url": "<URL OF TOWER SERVER>",
          "displayname": "RHSSO"
        }
      }
    * SAML Service Provider Technical Contact:
      ```
      {
        "emailAddress": "technical.contact@acme.com",
        "givenName": "Technical Contact"
      }
    * SAML Service Provider Support Contact:
      ```
      {
       "emailAddress": "support.contant@acme.com",
       "givenName": "Support Contact"
      }
    * SAML Enabled Identity Providers:
      ```
      {
        "RHSSO": {
          "attr_user_permanent_id": "name_id",
          "url": "<SSO SERVER URL>:<PORT IF NEEDED>/auth/realms/YOUR REALM/protocol/saml",
          "entity_id": "<SSO SERVER URL>:<PORT IF NEEDED>/auth/realms/YOUR REALM",
          "attr_email": "email",
          "attr_first_name": "first_name",
          "attr_last_name": "last_name",
          "attr_username": "username",
          "attr_groups": "groups",
          "x509cert": "<PASTE THE X509 PUBLIC CERT HERE IN ONE, NON-BREAKING LINE>"
        }
      }
    * SAML Organization Map:
      ```
      {
        "Default": {
          "users": true
        },
        "Systems Engineering": {
          "remove_admins": false,
          "remove_users": false,
          "users": true,
          "admins": [
            "admin.1@acme.com"
          ]
        }
      }
    * SAML Organization Attribute Mapping:
      ```
      {}
    * SAML Team Map:
      ```
      null
    * SAML Security Config:
      ```
      {
        "requestedAuthnContext": false
      }
    * SAML Service Provider extra configuration data:
      ```
      null
    * SAML IDP to extra_data attribute mapping:
      ```
      null
    * Click Save
    * If done properly, the log-in screen for Ansible Controller should show a user icon under the "Log In" button. This will redirect you to SSO sign-in.


## Useful links
[Red Hat Single Sign-on Integration with Ansible Tower](https://www.ansible.com/blog/red-hat-single-sign-on-integration-with-ansible-tower)

[Configuring Ansible Tower/AWX with RedHat SSO / Keycloak](https://josh-tracy.github.io/Ansible_Tower_RedHatSSO/)

[Summary of Authentication Methods For Red Hat Ansible Tower](https://www.ansible.com/blog/summary-of-authentication-methods-in-red-hat-ansible-tower)

[SAML](https://github.com/ansible/awx/blob/devel/docs/auth/saml.md)

[Configuring Keycloak (SAML)](https://www.rancher.co.jp/docs/rancher/v2.x/en/admin-settings/authentication/keycloak/)
