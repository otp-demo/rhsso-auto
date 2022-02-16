# RH-SSO integration with Azure

## Introduction
The purpose of this readme is to provide step by step guide to integrate RH-SSO with Microsoft Azure. After your RH-SSO instance is deployed you can use below guide to implement SAML SSO between RH-SSO (IdP) and Microsoft Azure (SP). You can automate the deployment of realm client for Azure via Jobs and ArgoCD but due to dependency on Windows OS and a requirement to complete one-off domain federation on Azure side, ideally below configuration should be completed manually by a Global Administrator on Azure side. For the purposes of this guide, we will be using `acme.com` as an example, you can use any domain that you own to federate with Microsoft Azure.

## Solution Overview

![Alt text](../images/azure-saml-rhsso.png?raw=true "Azure SAML SSO - Azure SP")

## Prerequisites 
- Working RH-SSO instance
- Global Administrator access on Azure to federate domain
- Windows OS to install and run PowerShell script

## Configuration

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

  > Global Administrator running this script should go through all the comments in `IdPFederation.ps1` file and update variables as required.

If run successfully, you should be able to use RH-SSO as IdP for signing into Azure portal.


⚠️ Users must be added manually on Azure Active Directory (AAD) using `New-MsolUser` command and with correct `ImmutableId` - please refer to comments on `IdPFederation.ps1` for more details. For example, if you have a user John Smith on RH-SSO, you must assign attribute with key `saml.persistent.name.id.for.urn:federation:MicrosoftOnline` and `somerandomstring` as value on RH-SSO. You will then have to manually create this user in AAD and use same random string as value for `ImmutableId`. Sample of complete `New-MsolUser` command can be found at the bottom of `IdPFederation.ps1` script. 

⚠️ RBAC for each user must be configured on Microsoft Azure. Azure role-based access control (Azure RBAC) has several Azure built-in roles that you can assign to users that are federated from custom domain. You can learn more about built-in roles here: [Azure built-in roles](https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles). Please also review how to assign roles roles using Azure portal here: [How to assign Azure roles using the Azure portal](https://docs.microsoft.com/en-us/azure/role-based-access-control/role-assignments-portal?tabs=current)





## Useful links
[Set up a trust between your SAML identity provider and Azure AD](https://docs.microsoft.com/en-us/azure/active-directory/hybrid/how-to-connect-fed-saml-idp#set-up-a-trust-between-your-saml-identity-provider-and-azure-ad)

[Use a SAML 2.0 Identity Provider (IdP) for Single Sign On](https://docs.microsoft.com/en-us/azure/active-directory/hybrid/how-to-connect-fed-saml-idp)

[Provision user principals to Azure AD / Microsoft 365](https://docs.microsoft.com/en-us/azure/active-directory/hybrid/how-to-connect-fed-saml-idp#provision-user-principals-to-azure-ad--microsoft-365)

[Using Keycloak as IdP for Azure AD](https://keycloak.discourse.group/t/using-keycloak-as-idp-for-azure-ad/10449)

[Get IdP Settings from Service Provider](https://gist.github.com/AlainODea/7bc9a0e6c04a19606eeaa4f0b99b8893)
