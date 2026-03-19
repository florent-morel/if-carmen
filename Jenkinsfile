@Library(['pipeline-framework', 'pipeline-toolbox']) _

withCredentials([
  azureServicePrincipal(credentialsId: 'DAC_AZURE_PRINCIPAL', clientIdVariable: 'CLIENT_ID', clientSecretVariable: 'CLIENT_SECRET',tenantIdVariable: 'TENANT_ID')]){
    workflow('forge', [
      pre_docker_publish: {
          stage("Public with latest tag") {
            sh 'docker tag dockerhub.rnd.amadeus.net/acfc-docker-dev-cb-test-nce/carbon-engine-webapp:$VERSION dockerhub.rnd.amadeus.net/acfc-docker-dev-cb-test-nce/carbon-engine-webapp:latest'
            sh 'docker push dockerhub.rnd.amadeus.net/acfc-docker-dev-cb-test-nce/carbon-engine-webapp:latest'
        }
      }
    ])
}
