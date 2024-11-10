param name string
param location string
param resourceToken string
param tags object
@secure()
param databasePassword string
@secure()
param secretKey string

var prefix = '${name}-${resourceToken}'
var pgServerName = '${prefix}-postgres-server'
var databaseSubnetName = 'database-subnet'
var webappSubnetName = 'webapp-subnet'
// Ensure storage account name meets minimum length requirements
var storageAccountName = take(replace(replace(toLower('${prefix}storage'), '-', ''), '_', ''), 24)
var minLength = length(storageAccountName) < 3 ? '${storageAccountName}str' : storageAccountName

// Virtual Network
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2019-11-01' = {
  name: '${prefix}-vnet'
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: databaseSubnetName
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
      {
        name: webappSubnetName
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
    ]
  }
}

resource databaseSubnet 'Microsoft.Network/virtualNetworks/subnets@2019-11-01' existing = {
  parent: virtualNetwork
  name: databaseSubnetName
}

resource webappSubnet 'Microsoft.Network/virtualNetworks/subnets@2019-11-01' existing = {
  parent: virtualNetwork
  name: webappSubnetName
}

// Private DNS Zone
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${pgServerName}.private.postgres.database.azure.com'
  location: 'global'
  tags: tags
}

resource privateDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: '${pgServerName}-link'
  parent: privateDnsZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetwork.id
    }
  }
}

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2021-08-01' = {
  name: minLength
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: true
    supportsHttpsTrafficOnly: true
  }
}

// Add CORS rules to the blob service
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2021-08-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    cors: {
      corsRules: [
        {
          allowedOrigins: [
            'https://${webApp.properties.defaultHostName}'
            'http://localhost:3000'
            'http://localhost:8000'
          ]
          allowedMethods: [
            'GET'
            'HEAD'
            'OPTIONS'
          ]
          allowedHeaders: [
            '*'
          ]
          exposedHeaders: [
            '*'
          ]
          maxAgeInSeconds: 3600
        }
      ]
    }
  }
}

resource staticContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-08-01' = {
  parent: blobService
  name: 'static'
  properties: {
    publicAccess: 'Blob'
  }
}

resource mediaContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-08-01' = {
  parent: blobService
  name: 'media'
  properties: {
    publicAccess: 'Blob'
  }
}

var storageAccountKey = storageAccount.listKeys().keys[0].value


// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2021-03-01' = {
  name: '${prefix}-service-plan'
  location: location
  tags: tags
  sku: {
    name: 'B1'
  }
  properties: {
    reserved: true
  }
}

// Log Analytics
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

// Application Insights
module applicationInsights 'appinsights.bicep' = {
  name: 'applicationinsights'
  params: {
    prefix: prefix
    location: location
    tags: tags
    workspaceId: logAnalyticsWorkspace.id
  }
}

// Web App
resource webApp 'Microsoft.Web/sites@2022-03-01' = {
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
    }
    httpsOnly: true
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Consolidated App Settings
resource webAppSettings 'Microsoft.Web/sites/config@2022-03-01' = {
  parent: webApp
  name: 'appsettings'
  properties: {
    // Build settings
    SCM_DO_BUILD_DURING_DEPLOYMENT: 'true'
    ENABLE_ORYX_BUILD: 'true'
    
    // Application settings
    AZURE_POSTGRESQL_CONNECTIONSTRING: 'dbname=${pythonAppDatabase.name} host=${postgresServer.name}.postgres.database.azure.com port=5432 sslmode=require user=${postgresServer.properties.administratorLogin} password=${databasePassword}'
    SECRET_KEY: secretKey
    WEBSITE_HTTPLOGGING_RETENTION_DAYS: '1'
    
    // Storage settings
    AZURE_STORAGE_ACCOUNT_NAME: storageAccount.name
    AZURE_STORAGE_ACCOUNT_KEY: storageAccount.listKeys().keys[0].value
    AZURE_STORAGE_CONTAINER: staticContainer.name
    AZURE_MEDIA_CONTAINER: mediaContainer.name
    
    // Python settings
    PYTHON_PATH: '/home/site/wwwroot'
    DJANGO_SETTINGS_MODULE: 'azureproject.production'
    
    // Web settings
    WEBSITES_PORT: '8000'
    WEBSITES_CONTAINER_START_TIME_LIMIT: '1800'
    
    // Application Insights
    APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING
  }
}

resource webAppLogs 'Microsoft.Web/sites/config@2022-03-01' = {
  parent: webApp
  name: 'logs'
  properties: {
    applicationLogs: {
      fileSystem: {
        level: 'Verbose'
      }
    }
    detailedErrorMessages: {
      enabled: true
    }
    failedRequestsTracing: {
      enabled: true
    }
    httpLogs: {
      fileSystem: {
        enabled: true
        retentionInDays: 1
        retentionInMb: 35
      }
    }
  }
}

resource webAppNetworkConfig 'Microsoft.Web/sites/networkConfig@2022-03-01' = {
  parent: webApp
  name: 'virtualNetwork'
  properties: {
    subnetResourceId: webappSubnet.id
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

resource pythonAppDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2022-01-20-preview' = {
  parent: postgresServer
  name: 'pythonapp'
}

// Outputs
output APPLICATIONINSIGHTS_CONNECTION_STRING string = applicationInsights.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING
output WEB_URI string = 'https://${webApp.properties.defaultHostName}'
output WEB_APP_SETTINGS array = [
  'SCM_DO_BUILD_DURING_DEPLOYMENT'
  'AZURE_POSTGRESQL_CONNECTIONSTRING'
  'SECRET_KEY'
  'WEBSITE_HTTPLOGGING_RETENTION_DAYS'
  'AZURE_STORAGE_ACCOUNT_NAME'
  'AZURE_STORAGE_ACCOUNT_KEY'
  'AZURE_STORAGE_CONTAINER'
  'AZURE_MEDIA_CONTAINER'
]
output WEB_APP_LOG_STREAM string = 'https://portal.azure.com/#@/resource${webApp.id}/logStream'
output WEB_APP_SSH string = 'https://${webApp.name}.scm.azurewebsites.net/webssh/host'
output WEB_APP_CONFIG string = 'https://portal.azure.com/#@/resource${webApp.id}/configuration'
