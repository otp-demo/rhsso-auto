# In order to configure Single Sign On for Azure as a Service Provider, we will need to federate a domain that will be used for KeyCloak.

# Step 0: Pre-requisite
# Before we run below script to federate, please ensure that a KeyCloak domain is added into Azure AD as a Custom Domain and is verified.
# An individual owning this custom domain will have to update TXT records on domain registrar.
# Access to Windows device is must. You cannot connect to MsolService from PowerShell running on any other OS (including Azure Cloud Shell).

# Step 1: Connect to MSOnline and federate custom domain
# After the custom domain is added to AAD, is verified and TXT records are added to domain registrar, run PowerShell scripts below for pulling SAML IdP and SP settings from metadata, via KeyCloak.
# You must update $FederationMetadataUri & $dom variables before running this script. FederationMetadataUri is where you can access your saml descriptor on KeyCloak and value for domain should the custom domain that you are using for KeyCloak.
# Download and install below required modules to successfully run this script.
# Install-Module MSOnline
# Install-Module AzureAD
# Install-Module AzureADPreview
# Import-Module MSOnline
# Connect-MsolService

# Step 2: Update variables
$dom = "acme.com"
$FederationMetadataUri = "https://keycloak.acme.com/auth/realms/sso/protocol/saml/descriptor"

# Step 3: Run script
# Get settings to enter on the Identity Provider (IdP) to allow authentication to Service Provider (SP)
function Get-SP-Settings-From-IdP($Metadata) {
    [xml]$IdPMetadata = $Metadata
    $IdPSingleSignOnURL = $IdPMetadata.EntityDescriptor.IDPSSODescriptor.SingleSignOnService |
    ? {$_.Binding -eq "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"} |
    % {$_.Location}
    $IdPIssuerURI = $IdPMetadata.EntityDescriptor.entityID
    $IdPSignatureCertificate = $IdPMetadata.EntityDescriptor.IDPSSODescriptor.KeyDescriptor |
    ? {$_.use -eq "signing"} |
    Select-Object -Last 1 |
    % {$_.KeyInfo.X509Data.X509Certificate}
}

# Fix for error "Could not establish trust relationship for the SSL/TLS secure channel." when running `Get-SP-Settings-From-IdP`
add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

# Get settings to enter on the Service Provider (SP) to have it trust your Identity Provider (IdP)
# KeyCloak is the IdP. 
Get-SP-Settings-From-IdP (Invoke-RestMethod -Uri $FederationMetadataUri)

# Set the domain federation for domain specified in $dom environment variable
$BrandName = "KeyCloak SAML 2.0 IDP"
$Protocol = "SAMLP"
Set-MsolDomainAuthentication `
  -DomainName $dom `
  -FederationBrandName $BrandName `
  -Authentication Federated `
  -PassiveLogOnUri $IdPSingleSignOnURL `
  -ActiveLogOnUri $IdPSingleSignOnURL `
  -SigningCertificate $IdPSignatureCertificate `
  -IssuerUri $IdPIssuerURI `
  -LogOffUri $IdPSingleSignOnURL `
  -PreferredAuthenticationProtocol $Protocol 

# New users can be added to Azure using following command. Uncomment and update as required
# In KeyCloak set attribute Key as "saml.persistent.name.id.for.urn:federation:MicrosoftOnline" and value as random 20+ characters string, copy this value and paste it here for -ImmutableId

# New-MsolUser `
#  -UserPrincipalName USER@acme.com `
#  -ImmutableId AttributeIDFromKeyCloak `
#  -DisplayName "User LastName" `
#  -FirstName User `
#  -LastName LastName `
#  -AlternateEmailAddresses "user@acme.com" `
#  -UsageLocation "US" 
