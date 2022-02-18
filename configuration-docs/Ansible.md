# RH-SSO integration with Ansible

## Introduction
The purpose of this readme is to provide step by step guide to integrate RH-SSO with Ansible Controller. The [**Automation**](#automation) section of this readme provides information regarding how to build and push an image to create Ansible client for RH-SSO and the [**Manual Configuration for Ansible integration**](#manual-configuration-for-ansible-integration) section provides details regarding configuration changes that you should make on Ansible side for a successful integration between Ansible (SP) and RH-SSO (IdP). 

You can automate the deployment of Ansible client via Jobs and Argo CD but SAML configuration on Ansible Controller must be done manually by Ansible Administrator. [**Manual Configuration for Ansible integration**](#manual-configuration-for-ansible-integration) provides steps that you must complete in order to successfully integrate Ansible with your RH-SSO instance.

## Prerequisites 
- Working RH-SSO instance
- Working Ansible Controller instance
- Administrator access for Ansible and RH-SSO
- Environment Variables from `argocd-configs` Config Map and `sso-configs` Secret

## Automation
You can automate deployment of Ansible client for RH-SSO using following:

* **Step 1: Create an image for deploying client**
  * First of all you will need to create an image using file [create-client-ansible.py](../create-client-ansible.py) which has all the required os, tools, and payload information to access RH-SSO api and create client. Please pay attention to environment variables that are in use and they must be available to successfully create Ansible client. As mentioned in prerequisites section, environment variables are stored in two differrent places ( `argocd-configs` Config Map and `sso-configs` Secret). A complete list of environment variables can be found at [Integration with RHSSO Environment Variables
](https://github.com/otp-demo/rhsso-auto#integration-with-rhsso-environment-variables).

* **Step 2: Run script to create an image and run from a Dockerfile**
  * After you are satisfied with variables, payload information etc. in [create-client-ansible.py](../create-client-ansible.py) file, you can use a script [config-ansible.sh](../config-ansible.sh) to run .py and create a Dockerfile that that installs [requirements](../requirements.txt) and runs [config-ansible.sh](../config-ansible.sh). For testing, you can also run it locally by setting local environment variables or storing them in .env file.
    * **Run locally**
      ```
      python3 create-client-ansible.py 
      ```
    * **Build as an image**
      Navigate to the root directory of this project and build the image using docker or podman and run the following command. Update repository name and image name as required in build and push commands.
      
      ```
      docker build -t quay.io/mahesh_v/ansible-keycloak-integration:v1 -f Dockerfile-ansible .
      docker push quay.io/mahesh_v/ansible-keycloak-integration:v1
      ``` 
* **Step 3: Running in Kubernetes or OpenShift**
  This script is designed to be ran as a Job in a Kubernetes-like environment. This Job will run a container containing this script once using the environment variables provided to it. You will likely need to push an image of this script with your payload attributes to a container registry that your cluster can reach. It is recommended that you get the admin username and password from a Secret or similarly secure resource.

  **Example Job**
  ```
  apiVersion: batch/v1
  kind: Job
  metadata:
    name: ansible-keycloak-integration
    namespace: sso-integration
  spec:
    template:
      spec:
       containers:
       - name: ansible-keycloak-integration
         image: quay.io/mahesh_v/ansible-keycloak-integration:v1
         envFrom:
         - configMapRef:
             name: argocd-configs
         - secretRef:
             name: sso-configs
         imagePullPolicy: Always
       restartPolicy: Never
    backoffLimit: 5

  ```
## Manual Configuration for Ansible integration
After client is setup on RH-SSO, next step is to configure Ansible SAML settings. Please complete below four steps to configure your Ansible instance to use RH-SSO as Identity Provider. 

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
