# Red Hat Single Sign-On (RH-SSO)

## Introduction
Red Hat Single Sign-On (RH-SSO) is based on the Keycloak project and enables you to secure your web applications by providing Web single sign-on (SSO) capabilities based on popular standards such as SAML 2.0, OpenID Connect and OAuth 2.0. The RH-SSO server can act as a SAML or OpenID Connect-based Identity Provider, mediating with your enterprise user directory or 3rd-party SSO provider for identity information and your applications via standards-based tokens. Configuration for each service listed below is different and it is recommended to familiarise yourself with each readme before attempting configuration:

|  Service | Automation  | Description  |
|--:|--|--|
| [Ansible Automation Controller](configuration-docs/Ansible.md)  | Semi-automated  | RH-SSO client creation and configuraiton is automated. Manul configuration on Ansible SAML setting is required.  |
| [Argo CD](configuration-docs/Argocd.md) | Fully-automated  | Both RH-SSO and ArgoCD are automated.  |
| [AWS](configuration-docs/AWS.md)  | Fully-automated  | Both RH-SSO and AWS are automated. IdP-initiated SAML flow. |
| [Azure](configuration-docs/Azure.md)  | Semi-automated  | RH-SSO client creation and configuraiton is automated. Configuration on Azure side is required  |
| [IBM Cloud](configuration-docs/IBM-cloud.md)  | Fully-manual  | RHSSO client, IBM Cloud IAM, and App ID configuration are all mnaul. (can be automted)  |
| [Vanilla OpenShift](configuration-docs/Openshift.md)  | Fully-automated  | Both RH-SSO and Openshift (vanilla cluster only) are automated.  |
| [Example App](https://github.com/akiyamn/rhsso-auto-deploy)  | Nil  |  Nil |


## Solution Overview

![Alt text](images/rh-sso-animated.gif?raw=true "RH-SSO Solution Overview")

> High-resolution version (.svg) of this diagram is available at [images/rh-sso-high-res.svg](images/rh-sso-high-res.svg)

Big shout out to [@Mahesh](https://github.com/maheshau1)

## How to Use
### Openshift/k8s environment
To run the job on Openshift or K8S, it is recommended to follow the [prerequisites](https://github.com/otp-demo/otp-gitops-services#rhsso-integration). The process is also described in [Solution-overview](#solution-overview). 
1. Create and push the image for the target service.
Example:
```bash
docker build -t quay.io/${username}/cluster-keycloak-integration:v1 -f Dockerfile-cluster .
docker push quay.io/${username}/cluster-keycloak-integration:v1
```
2. Create and deploy a job. Example:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: cluster-keycloak-integration
  namespace: sso-integration
spec:
  template:
    spec:
      containers:
      - name: cluster-keycloak-integration
        image: quay.io/${username}/cluster-keycloak-integration:v1
        imagePullPolicy: Always
        envFrom:
        - configMapRef:
            name: argocd-configs
        - secretRef:
            name: sso-configs
      restartPolicy: Never
  backoffLimit: 5
```
Notice the environment varialbes are provided by configmap `argocd-configs` and secret `sso-configs`. Details for each items are provided in [below section](#integration-with-rh-sso-environment-variables)

### Test locally
You can test the `.py` python files or shell scripts with following recommendation:
- python3.6+. Python 3.9
- Provide .env file that combines the [list of environment variables](#integration-with-rh-sso-environment-variables). Refer to example [.env](.env.example) file.




# Integration with RH-SSO Environment Variables
RH-SSO environment variables are used across different services (Ansible tower, Openshift cluster etc.), some are commonly used by all components, while some are used by a specific service. Details below. In openshift enviornment, environment variables are stored in two places: `confimap map: argocd-configs` (wrong name, will need to change in the future) and `secret: sso-configs` (Secret single source from vault with path `/rhsso/integration`).
Note: Location below indicates where the enviornment variables are stored in Openshift/K8s environment. Implementation can be found [here](https://github.com/otp-demo/otp-gitops-services).

| Name  | Location  | Service  |  Description
|---|---|---|---|
| MASTER_REALM | argocd-configs | Common | Master realm name, used to get access token |
| USER_NAME  | argocd-configs  | Common  | User name to get access token, automatically populated preporcessing job (TODO: This however should go to secret)  |
| PASSWORD  | argocd-configs  | Common  | Password to get access token, automatically populated preporcessing job (TODO: This however should go to secret). This is also the password to login the RHSSO UI |
| ADMIN_CLIENT_ID  | sso-configs  | Common  | Admin Client ID used to get the access token, it is normally a static name "admin-cli" across different RHSSO instances |
| KEYCLOAK_HOSTNAME  | sso-configs  | Common  | Keycloak root url |
| KEYCLOAK_REALM  | argocd-configs  | Common  | Tje target realm that will be created for all clients |
| ARGO_ROOT_URL  | argo-configs  | ArgoCD  | Root URL for ArgoCD |
| ARGO_CLIENT_ID  | argocd-configs  | ArgoCD  | Client ID/name, this is not a real ID, you can give it name you like |
| ARGO_GROUP_NAME  | argocd-configs  | ArgoCD  | The group created in RHSSO realm, and will be used for RBAC into Argocd. The admin group:  "ArgoCDAdmins" |
| ARGO_ADMIN_USERNAME  | sso-configs  | ArgoCD  | THe name for the user that will be created in the realm. This username will be used across different clients for login. The name is not reflective, and should be more general. |
| ARGO_ADMIN_PASSWORD  | sso-configs  | ArgoCD  | Password for the user. Again this is general. |
| ARGO_ADMIN_EMAIL | sso-configs  | ArgoCD  | User email. should be general. Note: for azure login, the email is suggested to have the same domain as the RHSSO |
| ARGO_ADMIN_FIRSTNAME | sso-configs  | ArgoCD  | User firstname. should be general. |
| ARGO_ADMIN_LASTNAME | sso-configs  | ArgoCD  | User lastname. should be general. |
| OPENSHIFT_OAUTH_NAME | argo-configs  | Openshift cluster  | The name that will be used to match configs between the openshift cluster and RHSSO. |
| CA_CERT_BUNDLE | sso-configs  | Openshift cluster  | The CA cert chain of trust for Keycloak/RHSSO |
| HTTP_DEBUG | argo-configs  | Common | To turn on DEBUG mode for http traffic, mainly for http contents (true/false) |
| TLS_VERIFY | argo-configs  | Common | Default to true. Can turn off in case the TLS is not available on RHSSO (true/false) |
| AZURE_CLIENT_ID | argo-configs  | Azure account | The client name for Azure client |
| AWS_CLIENT_SAML_URL | argo-configs  | AWS | The saml url to be imported into keycloak to create AWS client |
| AWS_ACCESS_KEY_ID | sso-configs  | AWS | Target aws accont key ID |
| AWS_SECRET_ACCESS_KEY | sso-configs  | AWS | Target aws accont Access Key |
| AWS_DEFAULT_REGION | sso-configs  | AWS | Target aws account default region |
| AWS_ID_PRODIVER_NAME | argo-configs  | AWS | ID provider name on AWS IAM |
| AWS_IAM_ROLE_POLICY_ARN | argo-configs  | AWS | The arn for aws policy for RHSSO user |
| AWS_IAM_ROLE_SESSION_DURATION | argo-configs  | AWS | Control how long the session will be valid for RHSSO user |
| KEYCLOAK_AWS_GROUP | argo-configs  | AWS | Group name created on Keycloak for aws |
| ANSIBLE_CLIENT_ID | argo-configs  | Ansible Tower | Client name/ID for Ansible created on RHSSO. This will be automatically populated |
| ANSIBLE_ACS_URL | argo-configs  | Ansible Tower | Automatically populated |
| ANSIBLE_HOST_URL | argo-configs  | Ansible Tower | Ansible root url.Automatically populated |
| ANSIBLE_REDIRECT_URI | argo-configs  | Ansible Tower | Automatically populated |
| ANSIBLE_CLIENT_SAML_URL | argo-configs  | Ansible Tower | Automatically populated. The content from the url will be imported into Keycloak |
| ANSIBLE_KEY_CERT | sso-configs  | Ansible Tower | Certificate generated manually, and provided to the Ansible configurations |
| ANSIBLE_KEY_PRIVATE_KEY | sso-configs  | Ansible Tower | Private key paired with ANSIBLE_KEY_CERT  |
| ANSIBLE_X509_CERT | sso-configs  | Ansible Tower | Content of ANSIBLE_KEY_CERT  |
