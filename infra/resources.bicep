param name string
param location string
param resourceToken string
param tags object
@secure()
param databasePassword string
@secure()
param secretKey string

var prefix = '${name}-${resourceToken}'

// Clean and Truncate Prefix for Storage Account Name
var cleanedPrefix = replace(prefix, '-', '')
var truncatedPrefix = substring(cleanedPrefix, 0, 17) // Ensures the total length <= 24
var storageAccountName = toLower('${truncatedPrefix}storage') // Ensures <=24 characters and no hyphens

// Define Variables
var databaseSubnetName = 'database-subnet'
var webappSubnetName = 'webapp-subnet'
var pgServerName = '${prefix}-postgres-server'

var mediaContainerName = 'media'

// Virtual Network
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2021-05-01' = {
  name: '${prefix}-vnet'
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
  }
}

// Database Subnet as a Child Resource
resource databaseSubnet 'Microsoft.Network/virtualNetworks/subnets@2021-05-01' = {
  name: databaseSubnetName
  parent: virtualNetwork
  properties: {
    addressPrefix: '10.0.0.0/24'
    delegations: [
      {
        name: '${prefix}-subnet-delegation'
        properties: {
          serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
        }
      }
    ]
  }
}

// Web App Subnet as a Child Resource
resource webappSubnet 'Microsoft.Network/virtualNetworks/subnets@2021-05-01' = {
  name: webappSubnetName
  parent: virtualNetwork
  properties: {
    addressPrefix: '10.0.1.0/24'
    delegations: [
      {
        name: '${prefix}-subnet-delegation-web'
        properties: {
          serviceName: 'Microsoft.Web/serverFarms'
        }
      }
    ]
  }
}

// Private DNS Zone for PostgreSQL
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${pgServerName}.private.postgres.database.azure.com'
  location: 'global'
  tags: tags
  dependsOn: [
    virtualNetwork
    databaseSubnet
    webappSubnet
  ]
}

// Link Private DNS Zone to Virtual Network
resource privateDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateDnsZone
  name: '${pgServerName}-link'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetwork.id
    }
  }
  dependsOn: [
    privateDnsZone
  ]
}

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    networkAcls: {
      bypass: 'AzureServices'
      virtualNetworkRules: [
        {
          id: databaseSubnet.id
        }
        {
          id: webappSubnet.id
        }
      ]
      defaultAction: 'Deny'
    }
    allowBlobPublicAccess: false
  }
  dependsOn: [
    databaseSubnet
    webappSubnet
  ]
}

// Blob Services
resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2022-09-01' = {
  parent: storageAccount
  name: 'default'
}

// Blob Container
resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  parent: blobServices
  name: mediaContainerName
  properties: {
    publicAccess: 'None'
  }
}

// Web App Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2021-03-01' = {
  name: '${prefix}-service-plan'
  location: location
  tags: tags
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  properties: {
    reserved: true
  }
}

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2020-03-01-preview' = {
  name: '${prefix}-workspace'
  location: location
  tags: tags
  properties: {
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
  }
}

// Application Insights Module
module applicationInsightsResources 'appinsights.bicep' = {
  name: 'applicationinsights-resources'
  params: {
    prefix: prefix
    location: location
    tags: tags
    workspaceId: logAnalyticsWorkspace.id
  }
}

// PostgreSQL Server
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2022-01-20-preview' = {
  name: pgServerName
  location: location
  tags: tags
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '13'
    administratorLogin: 'postgresadmin'
    administratorLoginPassword: databasePassword
    storage: {
      storageSizeGB: 128
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    network: {
      delegatedSubnetResourceId: databaseSubnet.id
      privateDnsZoneArmResourceId: privateDnsZone.id
    }
    highAvailability: {
      mode: 'Disabled'
    }
    maintenanceWindow: {
      customWindow: 'Disabled'
      dayOfWeek: 0
      startHour: 0
      startMinute: 0
    }
  }

  dependsOn: [
    privateDnsZoneLink
  ]
}

// PostgreSQL Database
resource pythonAppDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2022-01-20-preview' = {
  parent: postgresServer
  name: 'pythonapp'
}

// Web App
resource web 'Microsoft.Web/sites@2022-03-01' = {
  name: '${prefix}-app-service'
  location: location
  tags: union(tags, { 'azd-service-name': 'web' })
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      alwaysOn: true
      linuxFxVersion: 'PYTHON|3.11'
      ftpsState: 'Disabled'
      appCommandLine: 'startup.sh'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'AZURE_POSTGRESQL_CONNECTIONSTRING'
          value: 'dbname=${pythonAppDatabase.name} host=${postgresServer.name}.postgres.database.azure.com port=5432 sslmode=require user=${postgresServer.properties.administratorLogin} password=${databasePassword}'
        }
        {
          name: 'SECRET_KEY'
          value: secretKey
        }
        {
          name: 'FLASK_DEBUG'
          value: 'False'
        }
        // Azure Storage Settings
        {
          name: 'AZURE_STORAGE_ACCOUNT_NAME'
          value: storageAccount.name
        }
        // Removed AZURE_STORAGE_CONNECTION_STRING to enhance security
        {
          name: 'MEDIA_CONTAINER_NAME'
          value: blobContainer.name
        }
      ]
    }
    httpsOnly: true
  }
  identity: {
    type: 'SystemAssigned'
  }

  // Removed explicit dependsOn entries
}

// Diagnostic Settings for Web App
resource webdiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'AllLogs'
  scope: web
  properties: {
    workspaceId: logAnalyticsWorkspace.id
    logs: [
      {
        category: 'AppServiceHTTPLogs'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'AppServiceConsoleLogs'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'AppServiceAppLogs'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'AppServiceAuditLogs'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'AppServiceIPSecAuditLogs'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'AppServicePlatformLogs'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
    ]
  }
}

// Web App App Settings as a Separate Resource
resource webAppSettings 'Microsoft.Web/sites/config@2022-03-01' = {
  name: 'appsettings'
  parent: web
  properties: {
    // Additional app settings can be added here if needed
  }
}

// Outputs
output WEB_URI string = 'https://${web.properties.defaultHostName}'
output APPLICATIONINSIGHTS_CONNECTION_STRING string = applicationInsightsResources.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING

// Removed WEB_APP_SETTINGS output to fix the compilation error

output WEB_APP_LOG_STREAM string = 'https://${web.properties.defaultHostName}/api/logs/stream'
output WEB_APP_SSH string = 'https://${web.properties.defaultHostName}/ssh'
output WEB_APP_CONFIG object = web.properties.siteConfig

output STORAGE_ACCOUNT_NAME string = storageAccount.name
output MEDIA_CONTAINER_NAME string = blobContainer.name
