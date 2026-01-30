param location string
param abbrs object
param resourceToken string
param tags object
param userAssignedManagedIdentityPrincipalId string
param principalId string
param secrets array
param doRoleAssignments bool

@description('Type of the principal - User for human users, ServicePrincipal for apps/managed identities')
param principalType string = 'User'

module vault 'br/public:avm/res/key-vault/vault:0.12.1' = {
  name: 'vault'
  params: {
    name: '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    roleAssignments: doRoleAssignments ? [
      {
        principalId: userAssignedManagedIdentityPrincipalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Key Vault Secrets Officer'
      }
      {
        principalId: principalId
        principalType: principalType
        roleDefinitionIdOrName: 'Key Vault Secrets Officer'
      }
    ] : []
    secrets: secrets
    enablePurgeProtection: false
    tags: tags
  }
}

output AZURE_RESOURCE_KEY_VAULT_ID string = vault.outputs.resourceId
output AZURE_RESOURCE_KEY_VAULT_NAME string = vault.outputs.name
