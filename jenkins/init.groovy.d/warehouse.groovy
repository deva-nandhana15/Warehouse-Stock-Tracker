import jenkins.model.Jenkins
import hudson.model.Result
import hudson.model.TaskListener
import hudson.model.listeners.RunListener
import hudson.plugins.git.GitSCM
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.job.WorkflowRun
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import groovy.json.JsonOutput

// Keep the standard security realm, setup wizard, CSRF protection and credentials
// untouched. No administrator passwords or tokens are read by this bootstrap.
def instance = Jenkins.get()
instance.setLabelString('docker-linux')
instance.setNumExecutors(1)
def name = 'Warehouse-Stock-Tracker'
def job = instance.getItem(name)
if (job == null) {
    job = instance.createProject(WorkflowJob, name)
    def scm = new GitSCM('https://github.com/deva-nandhana15/Warehouse-Stock-Tracker.git')
    scm.branches = [new hudson.plugins.git.BranchSpec('*/main')]
    def definition = new CpsScmFlowDefinition(scm, 'Jenkinsfile')
    definition.setLightweight(true)
    job.setDefinition(definition)
    job.setDescription('Local Docker CI; security gates active; publishing and Azure deployment require explicit configuration.')
    job.save()
}
instance.save()

// Export only build verification metadata. This allows CLI verification without
// reading Jenkins credentials or making anonymous access available.
class WarehouseBuildEvidence extends RunListener<WorkflowRun> {
    WarehouseBuildEvidence() { super(WorkflowRun.class) }
    @Override
    void onCompleted(WorkflowRun run, TaskListener listener) {
        if (run.parent.name != 'Warehouse-Stock-Tracker') return
        def result = [job: run.parent.name, number: run.number,
                      result: run.result?.toString(), duration_ms: run.duration,
                      url: "http://localhost:8080/${run.url}"]
        def output = new File(Jenkins.get().rootDir, 'warehouse-build-status.json')
        output.text = JsonOutput.prettyPrint(JsonOutput.toJson(result))
    }
}
RunListener.all().add(new WarehouseBuildEvidence())
def request = new File(instance.rootDir, 'warehouse-run-request')
if (job.lastBuild == null || request.exists()) {
    job.scheduleBuild2(10)
    if (request.exists()) request.delete()
}
