targetScope = 'resourceGroup'

@description('Azure region for all Lab 0 resources. eastus2 is the workshop default because the required Cohere and OpenAI models have been validated there.')
param location string = 'eastus2'

@description('Name of the Microsoft Foundry account. This is a Microsoft.CognitiveServices/accounts resource with kind=AIServices.')
param foundryAccountName string

@description('Name of the Foundry project child resource.')
param foundryProjectName string

@description('Name of the workspace-based Application Insights component used by Lab 1 monitoring.')
param appInsightsName string

@description('Name of the Log Analytics workspace backing Application Insights.')
param logAnalyticsName string

@description('Declarative model deployments to create on the Foundry account.')
param deployments array

// Foundry projects live under an AIServices account; the S0 SKU supports the workshop deployments.
resource account 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: foundryAccountName
  location: location
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    allowProjectManagement: true
    customSubDomainName: foundryAccountName
  }
}

// The project resource scopes Lab 1 agents, evaluations, and tracing to one workshop workspace.
resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: account
  name: foundryProjectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: foundryProjectName
  }
}

// Deploy models one at a time to reduce quota/rate-limit collisions during class setup.
@batchSize(1)
resource modelDeployments 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = [for deployment in deployments: {
  parent: account
  name: deployment.name
  sku: {
    name: deployment.skuName
    capacity: deployment.capacity
  }
  properties: {
    model: {
      format: deployment.modelFormat
      name: deployment.modelName
      version: deployment.modelVersion
    }
  }
}]

// Application Insights stores traces in Log Analytics so learners can inspect agent calls after Lab 1.
resource workspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
  }
}

// setup-env.sh reads these outputs/resource names to populate the notebook .env file.
output foundryAccountName string = account.name
output foundryProjectName string = project.name
output foundryEndpoint string = account.properties.endpoint
output projectEndpoint string = '${account.properties.endpoint}api/projects/${project.name}'
output appInsightsConnectionString string = appInsights.properties.ConnectionString
