# RH-SSO integration with Argo CD

## Introduction
After your RH-SSO instance is deployed you should see that client for Argo CD is already configured. Below guide briefly explains how Argo CD client works with RH-SSO. If you need to manually configure RH-SSO for Argo CD, you can refer to this guide: [SSO Integration for the OpenShift GitOps Operator](https://cloud.redhat.com/blog/sso-integration-for-the-openshift-gitops-operator). Please note that the settings mentioned in this readme should be used as a guide only, each environment and its security requirement is differrent and as a result, please adapt and change settings as required.

## Prerequisites 
- Working RH-SSO instance
- Working Argo CD instance
- Administrator access for RH-SSO and Argo CD
- Environment Variables from `argocd-configs` Config Map and `sso-configs` Secret

## Configuration
* **Step 1: Find your Argo CD server route**
  * If Argo CD server was deployed via GitOps pattern on OpenShift, you can execute following commands to get details about your server route
    ```
    oc get route <instance-name>-server -n <namespace>
    ```
    For example, for the out-of-the-box (OOTB) Argo CD instance under openshift-gitops namespace, the command to find the Argo CD server route is:
    ```
    oc get route openshift-gitops-server -n openshift-gitops
    ```    
* **Step 2: Login to your RH-SSO Server and check if client is correctly configured**
  * Using GitOps pattern a client should automatically get deployed onto your RH-SSO instance for Argo CD
  * Logon to your RH-SSO instance and check following:
    * Under your realm, check if a client named `argocd` exist
    
* **Step 3: Open Argo CD client and check following**
  * Client ID: `argocd`
  * Enabled: `On`
  * Client Protocol: `openid-connect`
  * Access Type: `confidential`
  * Standard Flow Enabled: `On`
  * Implicit Flow Enabled: `Off`
  * Direct Access Grants Enabled: `On`
  * Service Accounts Enabled: `Off`
  * OAuth 2.0 Device Authorization Grant Enabled: `Off`
  * OIDC CIBA Grant Enabled: `Off`
  * Authorization Enabled: `Off`
  * Root URL: `<URL/Route that you found in step 1>`
  * Web Origins: `<URL/Route that you found in step 1>`
  * Backchannel Logout Session Required: `On`
  * Backchannel Logout Revoke Offline Sessions: `Off`
  * Fine Grain OpenID Connect Configuration:
    * User Info Signed Response Algorithm: `unsigned`
    * Request Object Signature Algorithm: `any`
    * Request Object Encryption Algorithm: `any`
    * Request Object Content Encryption Algorithm: `any`
    * Request Object Required: `not required`
  * OpenID Connect Compatibility Modes
    * Exclude Session State From Authentication Response: `Off`
    * Use Refresh Tokens: `On`
    * Use Refresh Tokens For Client Credentials Grant: `Off`

* **Step 4: Check Group Claims and Admin Group**
  * To manage users in Argo CD, you must configure a groups claim that can be included in the authentication token. Similar to above, Group Claim should already be configured via GitOps but you can follow below steps to ensure that everything is in order:
    * Check if Client Scope called `groups` exists and settings are configured as following:
      * Name: `groups`
      * Protocol: `openid-connect`
      * Display On Consent Screen: `On`
      * Indclude In Tocken Scope: `On`
    * Click on Mappers tab, open `groups` mapper and check if following is correctly configured
      * Protocol: `openid-connect` (greyed out)
      * Name: `groups` (greyed out)
      * Mapper Type: `Group Membership` (greyed out)
      * Token Claim Name: `groups`
      * Full group path: `Off`
      * Add to ID token: `On`
      * Add to access token: `On`
      * Add to userinfo: `On`
  * Check if Client is configured to provide the `groups` scope:
    * Click on Clients and select `argocd` client
    * Click on Client Scopes and under Default Client Scopes, ensure that `groups` client scope is in Assigned Default Client Scopes
  * Navigate to Groups and check if a group called `ArgoCDAdmins` exists
    * Open `ArgoCDAdmins` group and check if user `admin` is a member of this group
* **Step 5: Check Argo CD OpenID Connect (OIDC) Configuration**
  * Check if the the data `oidc.keycloak.clientSecret` exist in your argocd-secret
    ```
    oc describe secret argocd-secret -n openshift-gitops
    ```
  * Check if the the data `oidc.keycloak.clientSecret` exist in your argocd-secret
    ```
    oc get argocd -o jsonpath="{.items[0].spec.oidcConfig}"
    ```
If all of above configuration is in place, you should see a Login Via Keycloak button when you visit Argo CD web interface. If you encounter any issues or if configuration is not in place, you either refer to Useful links below and make changes to code as required.
## Useful links
[SSO Integration for the OpenShift GitOps Operator](https://cloud.redhat.com/blog/sso-integration-for-the-openshift-gitops-operator)

[Integrate Keycloak and ArgoCD within Kubernetes with ease](https://medium.com/geekculture/integrate-keycloak-and-argocd-within-kubernetes-with-ease-6871c620d3b3)
