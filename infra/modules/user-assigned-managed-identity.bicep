param location string
param abbrs object
param resourceToken string

@description('GitHub repository in format owner/repo')
param githubRepository string = 'mikefelder/gh-copilot-developer-impact-dashboard'

@description('GitHub environment name for federated credential')
param githubEnvironment string = 'demo'

module identity 'br/public:avm/res/managed-identity/user-assigned-identity:0.2.1' = {
  name: 'identity'
  params: {
    name: '${abbrs.managedIdentityUserAssignedIdentities}${resourceToken}'
    location: location
    federatedIdentityCredentials: [
      {
        name: 'github-${githubEnvironment}-federated-credential'
        audiences: [
          'api://AzureADTokenExchange'
        ]
        issuer: 'https://token.actions.githubusercontent.com'
        subject: 'repo:${githubRepository}:environment:${githubEnvironment}'
      }
    ]
  }
}

output AZURE_RESOURCE_USER_ASSIGNED_IDENTITY_ID string = identity.outputs.resourceId
output AZURE_RESOURCE_USER_ASSIGNED_IDENTITY_CLIENT_ID string = identity.outputs.clientId
output AZURE_RESOURCE_USER_ASSIGNED_IDENTITY_PRINCIPAL_ID string = identity.outputs.principalId
output AZURE_RESOURCE_USER_ASSIGNED_IDENTITY_NAME string = identity.outputs.name
