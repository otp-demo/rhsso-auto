# RH-SSO integration with Azure

## Introduction
The purpose of this readme is to provide step by step guide to integrate RH-SSO with Microsoft Azure. The [**Automation**](#automation) section of this readme provides information regarding how to build and push an image to create Azure client for RH-SSO and the [**Manual Configuration for Azure integration**](#manual-configuration-for-azure-integration) section provides details regarding configuration changes that you should make on Azure side for a successful integration between Azure (SP) and RH-SSO (IdP). 

You can automate the deployment of Azure client via Jobs and Argo CD but due to dependency on Windows OS (to run `MSOnline` cmdlets) and a requirement to complete one-off domain federation on Azure side, ideally [**Manual Configuration for Azure integration**](#manual-configuration-for-azure-integration) section of this readme should be completed manually by a Global Administrator on Azure side.

> For the purposes of this guide, we will be using `acme.com` as an example, you can use any domain that you own to federate with Microsoft Azure.

## Solution Overview

![Alt text](../images/azure-saml-rhsso.png?raw=true "Azure SAML SSO - Azure SP")

## Prerequisites 
- Working RH-SSO instance
- Global Administrator access on Azure to federate domain
- Windows OS to install and run PowerShell script
- Environment Variables from `argocd-configs` Config Map and `sso-configs` Secret
## Automation
You can automate deployment of Azure client for RH-SSO using following:

* **Step 1: Create an image for deploying client**
  * First of all you will need to create an image using file [create-client-azure.py](../create-client-azure.py) which has all the required os, tools, and payload information to access RH-SSO api and create client. Please pay attention to environment variables that are in use and they must be available to successfully create Azure client. As mentioned in prerequisites section, environment variables are stored in two differrent places ( `argocd-configs` Config Map and `sso-configs` Secret). A complete list of environment variables can be found at [Integration with RHSSO Environment Variables
](https://github.com/otp-demo/rhsso-auto#integration-with-rhsso-environment-variables).

* **Step 2: Run script to create an image and run from a Dockerfile**
  * After you are satisfied with variables, payload information etc. in [create-client-azure.py](../create-client-azure.py) file, you can use a script [config-azure.sh](../config-azure.sh) to run .py and create a Dockerfile that that installs [requirements](../requirements.txt) and runs [config-azure.sh](../config-azure.sh). For testing, you can also run it locally by setting local environment variables or storing them in .env file.
    * **Run locally**
      ```
      python3 create-client-azure.py 
      ```
    * **Build as an image**
      Navigate to the root directory of this project and build the image using docker or podman and run the following command. Update repository name and image name as required in build and push commands.
      
      ```
      docker build -t quay.io/mahesh_v/azure-keycloak-integration:v1 -f Dockerfile-azure .
      docker push quay.io/mahesh_v/azure-keycloak-integration:v1
      ``` 
* **Step 3: Running in Kubernetes or OpenShift**
  This script is designed to be ran as a Job in a Kubernetes-like environment. This Job will run a container containing this script once using the environment variables provided to it. You will likely need to push an image of this script with your payload attributes to a container registry that your cluster can reach. It is recommended that you get the admin username and password from a Secret or similarly secure resource.

  **Example Job**
  ```
  apiVersion: batch/v1
  kind: Job
  metadata:
    name: azure-keycloak-integration
    namespace: sso-integration
  spec:
    template:
      spec:
       containers:
       - name: azure-keycloak-integration
         image: quay.io/mahesh_v/azure-keycloak-integration:v1
         envFrom:
         - configMapRef:
             name: argocd-configs
         - secretRef:
             name: sso-configs
         imagePullPolicy: Always
       restartPolicy: Never
    backoffLimit: 5

  ```
## Manual Configuration for Azure integration
After client is setup on RH-SSO, next step is to federate custom domain and run PowerShell script [IdPFederation.ps1](../IdPFederation.ps1). Please complete below three steps to configure your Microsoft Azure tenant to use RH-SSO as Identity Provider for your custom domain. 

* **Step 1: Add Custom Domain to AAD**
  * Sign in to the Azure portal using a **Global administrator** account for the directory.
  * Search for and select Azure Active Directory from any page. Then select Custom domain names > Add custom domain.
  * In Custom domain name, enter your organization's new name, for example, `acme.com`. Select Add domain.
  * The unverified domain is added. The `acme.com` page appears showing your DNS information. Save this information. You need it in the next step to create a TXT record to configure DNS.

* **Step 2: Add DNS information for your custom domain**

  After you add your custom domain name to Azure AD, you must return to your domain registrar and add the Azure AD DNS information from your copied TXT file. Creating this TXT record for your domain verifies ownership of your domain name.
  Go back to your domain registrar and create a new TXT record for your domain based on your copied DNS information. Set the time to live (TTL) to 3600 seconds (60 minutes), and then save the record.

    > After you register your custom domain name, make sure it's valid in Azure AD. The propagation from your domain registrar to Azure AD can be instantaneous or it can take a few days, depending on your domain registrar.

* **Step 3: Run PowerShell Script to enable federation**
  
  After above two steps are completed we are ready to federate `acme.com` domain to Azure tenancy. A sample script `IdPFederation.ps1` can be found in this repo. Running this script will allow RH-SSO users with a verified domain specified in `$dom` variable to sign into Azure Portal via RH-SSO as IdP.

  > Global Administrator running this script should go through all the comments in [IdPFederation.ps1](../IdPFederation.ps1) file and update variables as required.

If run successfully, you should be able to use RH-SSO as IdP for signing into Azure portal.


⚠️ Users must be added manually on Azure Active Directory (AAD) using `New-MsolUser` command and with correct `ImmutableId` - please refer to comments on [IdPFederation.ps1](../IdPFederation.ps1) for more details. For example, if you have a user John Smith on RH-SSO, you must assign attribute with key `saml.persistent.name.id.for.urn:federation:MicrosoftOnline` and `somerandomstring` as value on RH-SSO. You will then have to manually create this user in AAD and use same random string as value for `ImmutableId`. Sample of complete `New-MsolUser` command can be found at the bottom of `IdPFederation.ps1` script. 

⚠️ RBAC for each user must be configured on Microsoft Azure. Azure role-based access control (Azure RBAC) has several Azure built-in roles that you can assign to users that are federated from custom domain. You can learn more about built-in roles here: [Azure built-in roles](https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles). Please also review how to assign roles roles using Azure portal here: [How to assign Azure roles using the Azure portal](https://docs.microsoft.com/en-us/azure/role-based-access-control/role-assignments-portal?tabs=current)

## Useful links
[Set up a trust between your SAML identity provider and Azure AD](https://docs.microsoft.com/en-us/azure/active-directory/hybrid/how-to-connect-fed-saml-idp#set-up-a-trust-between-your-saml-identity-provider-and-azure-ad)

[Use a SAML 2.0 Identity Provider (IdP) for Single Sign On](https://docs.microsoft.com/en-us/azure/active-directory/hybrid/how-to-connect-fed-saml-idp)

[Provision user principals to Azure AD / Microsoft 365](https://docs.microsoft.com/en-us/azure/active-directory/hybrid/how-to-connect-fed-saml-idp#provision-user-principals-to-azure-ad--microsoft-365)

[Using Keycloak as IdP for Azure AD](https://keycloak.discourse.group/t/using-keycloak-as-idp-for-azure-ad/10449)

[Get IdP Settings from Service Provider](https://gist.github.com/AlainODea/7bc9a0e6c04a19606eeaa4f0b99b8893)
