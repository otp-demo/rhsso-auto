# Red Hat Single Sign-On (RH-SSO)

## Introduction
Red Hat Single Sign-On (RH-SSO) is based on the Keycloak project and enables you to secure your web applications by providing Web single sign-on (SSO) capabilities based on popular standards such as SAML 2.0, OpenID Connect and OAuth 2.0. The RH-SSO server can act as a SAML or OpenID Connect-based Identity Provider, mediating with your enterprise user directory or 3rd-party SSO provider for identity information and your applications via standards-based tokens. Configuration for each service listed below is different and it is recommended to familiarise yourself with each readme before attempting configuration:

[Ansible](configuration-docs/Ansible.md)

[Argo CD](configuration-docs/Argocd.md)

[AWS](configuration-docs/AWS.md)

[Azure](configuration-docs/Azure.md)

[IBM Cloud](configuration-docs/IBM-cloud.md)

[OpenShift](configuration-docs/Openshift.md)

Big shout out to [@Mahesh](https://github.com/maheshau1)

# Integration with RHSSO Environment Variables
RHSSO environment variables are used across different services (Ansible tower, Openshift cluster etc.), some are commonly used by all components, while some are used by a specific service. Details below. In openshift enviornment, environment variables are stored in two places: `confimap map: argocd-configs` (wrong name will need to change later on) and `secret: sso-configs` (Secret single source from vault with path `/rhsso/integration`)

| Name  | Location  | Service  |  Comment
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
| HTTP_DEBUG | argo-configs  | Common | To turn on DEBUG mode for http traffic, mainly for http contents |
| TLS_VERIFY | argo-configs  | Common | Default to true. Can turn off in case the TLS is not available on RHSSO |
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
