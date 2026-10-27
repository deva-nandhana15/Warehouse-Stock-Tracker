pipeline {
    agent { label 'windows' }
    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 45, unit: 'MINUTES')
    }
    triggers { pollSCM('H/5 * * * *') }
    parameters {
        string(name: 'IMAGE_REPOSITORY', defaultValue: 'dva15/warehouse-stock-tracker', description: 'Public Docker Hub repository')
        booleanParam(name: 'PUBLISH_IMAGE', defaultValue: false, description: 'Publish an image only for the trusted main branch')
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.COMMIT_SHA = powershell(returnStdout: true, script: 'git rev-parse HEAD').trim()
                    if (!(env.COMMIT_SHA ==~ /[0-9a-f]{40}/)) { error('Invalid commit SHA') }
                    if (!(params.IMAGE_REPOSITORY ==~ /[a-z0-9_-]+\/[a-z0-9._-]+/)) { error('Invalid image repository') }
                    env.IMAGE_REF = "${params.IMAGE_REPOSITORY}:${env.COMMIT_SHA}"
                }
                powershell '''
                    . ./scripts/common.ps1
                    New-Item -ItemType Directory -Force reports | Out-Null
                    Invoke-Checked python @('-m', 'venv', '.venv')
                    Invoke-Checked ./.venv/Scripts/python.exe @('-m', 'pip', 'install', '-r', 'requirements-dev.txt', '-r', 'requirements-security.txt')
                    Invoke-Checked npm.cmd @('ci', '--ignore-scripts')
                '''
            }
        }
        stage('Test') {
            steps { powershell '''
                . ./scripts/common.ps1
                Invoke-Checked ./.venv/Scripts/python.exe @('-m', 'pytest', '-q', '--junitxml=reports/junit.xml')
            ''' }
        }
        stage('Secret scan') {
            steps { powershell '''
                . ./scripts/common.ps1
                $version = & gitleaks version
                if ($LASTEXITCODE -ne 0 -or "$version".Trim() -ne '8.30.1') { throw 'Expected Gitleaks 8.30.1' }
                Invoke-Checked gitleaks @('git', '.', '--redact', '--report-format', 'json', '--report-path', 'reports/gitleaks.json')
            ''' }
        }
        stage('Static and dependency scan') {
            steps { powershell '''
                . ./scripts/common.ps1
                $version = & trivy --version
                if ($LASTEXITCODE -ne 0 -or ($version -join ' ') -notmatch 'Version: 0\.76\.1(?:\s|$)') { throw 'Expected Trivy 0.76.1' }
                Invoke-Checked ./.venv/Scripts/python.exe @('-m', 'bandit', '-r', 'app', '-ll', '-f', 'json', '-o', 'reports/bandit.json')
                Invoke-Checked trivy @('fs', '--scanners', 'vuln', '--skip-dirs', '.venv,node_modules,.tools,.terraform', '--severity', 'CRITICAL', '--ignore-unfixed', '--exit-code', '1', '--format', 'json', '--output', 'reports/trivy-fs.json', '.')
            ''' }
        }
        stage('IaC checks') {
            steps { powershell '''
                . ./scripts/common.ps1
                Invoke-Checked terraform @('-chdir=terraform', 'fmt', '-check')
                Invoke-Checked terraform @('-chdir=terraform', 'init', '-backend=false', '-input=false', '-lockfile=readonly')
                Invoke-Checked terraform @('-chdir=terraform', 'validate', '-no-color')
                Invoke-Checked trivy @('config', '--severity', 'HIGH,CRITICAL', '--exit-code', '1', '--format', 'json', '--output', 'reports/trivy-config.json', 'terraform')
            ''' }
        }
        stage('Docker build') {
            steps { powershell '''
                . ./scripts/common.ps1
                Invoke-Checked docker @('build', '--pull', '-f', 'docker/Dockerfile', '-t', $env:IMAGE_REF, '.')
            ''' }
        }
        stage('Image scan') {
            steps { powershell '''
                . ./scripts/common.ps1
                Invoke-Checked trivy @('image', '--severity', 'CRITICAL', '--ignore-unfixed', '--exit-code', '1', '--format', 'json', '--output', 'reports/trivy-image.json', $env:IMAGE_REF)
            ''' }
        }
        stage('Container smoke and Newman') {
            steps { powershell './scripts/test-container.ps1 -Image $env:IMAGE_REF' }
        }
        stage('Push') {
            when { expression { params.PUBLISH_IMAGE && (env.BRANCH_NAME == 'main' || (!env.BRANCH_NAME && env.GIT_BRANCH == 'origin/main')) } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_TOKEN')]) {
                    powershell '''
                        . ./scripts/common.ps1
                        $env:DOCKER_CONFIG = Join-Path $env:TEMP ([guid]::NewGuid().ToString())
                        New-Item -ItemType Directory $env:DOCKER_CONFIG | Out-Null
                        try {
                            $env:REGISTRY_TOKEN | docker login --username $env:REGISTRY_USER --password-stdin
                            if ($LASTEXITCODE -ne 0) { throw 'Registry login failed' }
                            Invoke-Checked docker @('push', $env:IMAGE_REF)
                        } finally {
                            # Exact, newly created temporary credential directory; no recursive deletion.
                            $config = Join-Path $env:DOCKER_CONFIG 'config.json'
                            if (Test-Path -LiteralPath $config) { Remove-Item -LiteralPath $config -Force }
                            Remove-Item -LiteralPath $env:DOCKER_CONFIG -Force
                        }
                    '''
                }
            }
        }
        stage('Manual deployment handoff') {
            when { expression { params.PUBLISH_IMAGE && (env.BRANCH_NAME == 'main' || (!env.BRANCH_NAME && env.GIT_BRANCH == 'origin/main')) } }
            steps {
                writeFile file: 'reports/deployment.txt', text: "Image passed gates and was published: ${env.IMAGE_REF}\nFollow docs/runbook.md to review plan and deploy manually. No cloud resources were changed by Jenkins.\n"
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
