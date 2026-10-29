pipeline {
    agent { label 'docker-linux' }
    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 45, unit: 'MINUTES')
    }
    triggers { pollSCM('H/5 * * * *') }
    parameters {
        string(name: 'IMAGE_REPOSITORY', defaultValue: 'dva15/warehouse-stock-tracker', description: 'Public Docker Hub repository')
        booleanParam(name: 'PUBLISH_IMAGE', defaultValue: false, description: 'Publish only from the trusted main branch; requires dockerhub credentials')
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.COMMIT_SHA = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                    if (!(env.COMMIT_SHA ==~ /[0-9a-f]{40}/)) { error('Invalid commit SHA') }
                    if (!(params.IMAGE_REPOSITORY ==~ /[a-z0-9_-]+\/[a-z0-9._-]+/)) { error('Invalid image repository') }
                    env.IMAGE_REF = "${params.IMAGE_REPOSITORY}:${env.COMMIT_SHA}"
                }
                sh '''
                    set -eu
                    mkdir -p reports
                    python3 -m venv .venv
                    .venv/bin/python -m pip install -r requirements-dev.txt -r requirements-security.txt
                    npm ci --ignore-scripts
                    docker info >/dev/null
                '''
            }
        }
        stage('Test') {
            steps { sh '.venv/bin/python -m pytest -q --junitxml=reports/junit.xml' }
        }
        stage('Secret scan') {
            steps { sh '''
                set -eu
                test "$(gitleaks version)" = '8.30.1'
                gitleaks git . --redact --report-format json --report-path reports/gitleaks.json
            ''' }
        }
        stage('Static and dependency scan') {
            steps { sh '''
                set -eu
                trivy --version | grep -Fx 'Version: 0.76.1'
                .venv/bin/python -m bandit -r app -ll -f json -o reports/bandit.json
                trivy fs --scanners vuln --skip-dirs .venv,node_modules,.tools,terraform/.terraform --severity CRITICAL --ignore-unfixed --exit-code 1 --format json --output reports/trivy-fs.json .
            ''' }
        }
        stage('IaC checks') {
            steps { sh '''
                set -eu
                terraform -chdir=terraform fmt -check
                terraform -chdir=terraform init -backend=false -input=false -lockfile=readonly
                terraform -chdir=terraform validate -no-color
                trivy config --ignorefile .trivyignore.yaml --severity HIGH,CRITICAL --exit-code 1 --format json --output reports/trivy-config.json terraform
            ''' }
        }
        stage('Docker build') {
            steps { sh 'docker build --pull -f docker/Dockerfile -t "$IMAGE_REF" .' }
        }
        stage('Image scan') {
            steps { sh 'trivy image --scanners vuln --severity CRITICAL --ignore-unfixed --exit-code 1 --format json --output reports/trivy-image.json "$IMAGE_REF"' }
        }
        stage('Container smoke and Newman') {
            steps { sh '.venv/bin/python scripts/test-container.py "$IMAGE_REF"' }
        }
        stage('Persistent storage integration') {
            steps { sh '.venv/bin/python scripts/test-table-persistence.py' }
        }
        stage('Push') {
            when { expression { params.PUBLISH_IMAGE && (env.BRANCH_NAME == 'main' || (!env.BRANCH_NAME && env.GIT_BRANCH == 'origin/main')) } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_TOKEN')]) {
                    sh '''
                        set +x
                        set -eu
                        export DOCKER_CONFIG="$(mktemp -d)"
                        trap 'rm -f -- "$DOCKER_CONFIG/config.json"; rmdir -- "$DOCKER_CONFIG"' EXIT
                        printf '%s' "$REGISTRY_TOKEN" | docker login --username "$REGISTRY_USER" --password-stdin
                        docker push "$IMAGE_REF"
                    '''
                }
            }
        }
        stage('Manual deployment handoff') {
            when { expression { params.PUBLISH_IMAGE && (env.BRANCH_NAME == 'main' || (!env.BRANCH_NAME && env.GIT_BRANCH == 'origin/main')) } }
            steps {
                writeFile file: 'reports/deployment.txt', text: "Published image: ${env.IMAGE_REF}\nReview a Terraform plan before manual Azure deployment. Jenkins does not change Azure resources.\n"
            }
        }
    }
    post {
        always {
            junit testResults: 'reports/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'reports/*', allowEmptyArchive: true
        }
    }
}
