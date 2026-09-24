---
title: "PLEXOS Cloud → Amazon S3: A Repeatable Post-Simulation Export Recipe"
date: 2026-09-23
---

After spending hours trying -and failing- to connect PLEXOS Cloud with an AWS S3 bucket, I thought it was worth persisting the lessons learned so future me has it a little easier next time this task comes up.

The objective is simple:

> Run a PLEXOS Cloud simulation and automatically export its Parquet solution files to Amazon S3 when the simulation finishes.

The working pattern is:

```text
PLEXOS Cloud simulation
        ↓
Post-simulation tasks
        ↓
Locate the Parquet solution
        ↓
Create a temporary DataHub S3 connector
        ↓
Upload the Parquet files to Amazon S3 Bucket
        ↓
Delete the temporary connector
```

The recipe below starts from AWS and PLEXOS Cloud setup and ends with a repeatable post-simulation export.

The basic strategy is:

1. prove that PLEXOS Cloud DataHub can write one harmless file to S3;
2. persist the working AWS credentials as PLEXOS Cloud secrets;
3. start from a fast, known-good simulation;
4. use Linux post-simulation tasks to expose its Parquet output through the shared `/output` directory;
5. upload that directory to S3 through a temporary DataHub connector; and
6. inspect the post-simulation log and S3 output.

The Linux approach is intentional: it keeps the actual post-simulation workflow to shell commands and the PLEXOS Cloud CLI, without requiring an uploaded Python script or an awkward inline Python command.

# Before starting

You will need:

* PLEXOS Cloud CLI (`pxc`) installed and authenticated on your local machine;
* permission to create and delete DataHub connectors;
* permission to create PLEXOS Cloud secrets;
* permission to enqueue simulations with post-simulation tasks;
* an Amazon S3 bucket;
* an AWS access key ID and secret access key for an identity allowed to write to that bucket; and
* a **fast, known-good, single-model PLEXOS Cloud simulation that produces Parquet output**.

The simulation itself is not what we are testing. Ideally, use something tiny that finishes quickly so the post-simulation tasks can be iterated without waiting on a substantive model run.

The Linux approach documented here also assumes the output structure observed in my test:

```text
version2/ParquetUploads
```

If that structure changes, the commands that locate the Parquet directory will need to change as well.

# Part 1 — Set up S3 access

## 1. Give the AWS writer the required permissions

The following IAM policy was sufficient for the DataHub connector in my test.

Replace `<S3_BUCKET_NAME>` with the bucket that will receive the PLEXOS outputs.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DataHubBucketOperations",
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketLocation",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads"
      ],
      "Resource": "arn:aws:s3:::<S3_BUCKET_NAME>"
    },
    {
      "Sid": "DataHubStagingAndExportObjectOperations",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:AbortMultipartUpload",
        "s3:ListMultipartUploadParts"
      ],
      "Resource": [
        "arn:aws:s3:::<S3_BUCKET_NAME>/energyexemplar_temp_uploads/*",
        "arn:aws:s3:::<S3_BUCKET_NAME>/plexos/solutions/*"
      ]
    }
  ]
}
```

One non-obvious requirement is:

```text
energyexemplar_temp_uploads/*
```

DataHub used this prefix for staging during the upload.

The final exports in this recipe go under:

```text
plexos/solutions/*
```

# Part 2 — Prove DataHub can write to S3

Do this before involving a simulation.

If a one-file DataHub upload does not work, adding post-simulation tasks only gives you more things to debug at once.

## 2. Confirm the connector feature

Open **Windows PowerShell** on the computer where the PLEXOS Cloud CLI is installed.

Copy and paste this entire block:

```powershell
pxc datahub connector feature-status
pxc datahub connector list --format json
```

The connector feature should be active.

The connector list itself may be empty.

## 3. Store the AWS credentials locally

Still in PowerShell, copy and paste:

```powershell
$credentialFolder = Join-Path $env:USERPROFILE ".plexos-s3-poc"

New-Item `
  -ItemType Directory `
  -Force `
  -Path $credentialFolder | Out-Null

notepad (Join-Path $credentialFolder "aws_access_key_id.txt")
notepad (Join-Path $credentialFolder "aws_secret_access_key.txt")
```

Two Notepad windows will open.

In:

```text
aws_access_key_id.txt
```

paste only the AWS access key ID.

In:

```text
aws_secret_access_key.txt
```

paste only the AWS secret access key.

Save both files and close Notepad.

These local files will also be used later to create the PLEXOS Cloud secrets.

## 4. Configure the connector test

In PowerShell, edit the first two values below and then paste the **entire block**:

```powershell
$bucketName = "<YOUR_S3_BUCKET_NAME>"
$awsRegion = "<YOUR_AWS_REGION>"

$stamp = Get-Date -Format "yyyyMMddHHmmss"

$connectorName = "PLEXOS_S3_TEST_$stamp"

$remoteFolder = `
  "connectors/AmazonS3/$connectorName/plexos/solutions/connector-test-$stamp"

$probeName = "connector-test-$stamp.txt"
$probePath = Join-Path $env:TEMP $probeName

Set-Content `
  -Path $probePath `
  -Value "PLEXOS Cloud DataHub connector test $stamp"

Write-Host "Connector: $connectorName"
Write-Host "DataHub destination: $remoteFolder"
Write-Host "Expected S3 key: plexos/solutions/connector-test-$stamp/$probeName"
```

Leave this PowerShell window open. The variables created above are used by the next steps.

## 5. Create the temporary DataHub connector

Copy and paste this entire block into the **same PowerShell window**:

```powershell
$accessKeyFile = `
  Join-Path $credentialFolder "aws_access_key_id.txt"

$secretKeyFile = `
  Join-Path $credentialFolder "aws_secret_access_key.txt"

$accessKey = `
  (Get-Content -Path $accessKeyFile -Raw).Trim()

$secretKey = `
  (Get-Content -Path $secretKeyFile -Raw).Trim()

if (
  [string]::IsNullOrWhiteSpace($accessKey) -or
  [string]::IsNullOrWhiteSpace($secretKey)
) {
  throw "The AWS credential files must each contain one non-empty value."
}

pxc datahub connector create `
  --name $connectorName `
  --connector-type AmazonS3 `
  --auth-type AccountCreds `
  --s3-access-key $accessKey `
  --s3-secret-key $secretKey `
  --region $awsRegion `
  --bucket-name $bucketName `
  --format json

Remove-Variable accessKey, secretKey
```

Connector creation should succeed before proceeding.

## 6. Upload one test file

Copy and paste:

```powershell
pxc datahub upload `
  --local-folder $env:TEMP `
  --remote-folder $remoteFolder `
  --pattern $probeName `
  --is-versioned false `
  --parallel-upload false `
  --format json
```

The expected result includes:

```text
Uploading SUCCESS for <local-file>
```

The following option matters:

```text
--is-versioned false
```

Connector paths do not support versioned DataHub resources.

## 7. Find the file in S3

Open the S3 bucket and look for:

```text
plexos/solutions/connector-test-<timestamp>/<file-name>
```

Notice that the DataHub destination was:

```text
connectors/AmazonS3/<connector-name>/plexos/solutions/...
```

but the physical S3 destination is:

```text
s3://<bucket>/plexos/solutions/...
```

The:

```text
connectors/AmazonS3/<connector-name>/
```

portion is a DataHub logical prefix. It does not become part of the S3 object key.

Once the file exists in S3, the AWS/DataHub side of the workflow is working.

Delete the temporary connector:

```powershell
pxc datahub connector delete --name $connectorName
```

Deleting the connector does not delete the object already written to S3.

# Part 3 — Persist the AWS credentials in PLEXOS Cloud

The local test used credentials stored on your computer.

The post-simulation task will execute in PLEXOS Cloud, so the same credentials need to be available there.

## 8. Create PLEXOS Cloud secrets

The local credential files from Step 3 should still exist.

Open PowerShell and copy and paste this **entire block**:

```powershell
$credentialFolder = `
  Join-Path $env:USERPROFILE ".plexos-s3-poc"

$accessKey = (
  Get-Content `
    -Path (Join-Path $credentialFolder "aws_access_key_id.txt") `
    -Raw
).Trim()

$secretKey = (
  Get-Content `
    -Path (Join-Path $credentialFolder "aws_secret_access_key.txt") `
    -Raw
).Trim()

pxc secrets create `
  --name S3-access-key-post `
  --value $accessKey

pxc secrets create `
  --name S3-secret-key-post `
  --value $secretKey

Remove-Variable accessKey, secretKey
```

This creates two secrets persisted in the PLEXOS Cloud tenant:

```text
S3-access-key-post
S3-secret-key-post
```

Later, the simulation request binds them to environment variables inside the connector-creation task:

```text
S3_ACCESS_KEY
S3_SECRET_KEY
```

So there are three distinct things worth keeping straight:

```text
local credential file
        ↓
PLEXOS Cloud secret
        ↓
post-task environment variable
```

For example:

```text
aws_access_key_id.txt
        ↓
S3-access-key-post
        ↓
S3_ACCESS_KEY
```

# Part 4 — Start from a fast, known-good simulation

Do not build an entire simulation request manually just to test the S3 integration.

Start with a simulation that already runs successfully and quickly.

## 9. Find a simulation to clone

If you already know the simulation ID you want to use, skip to Step 10.

If you have not recently executed the fast model you want to use, execute it now, then proceed.

Otherwise, open PowerShell.

Replace `<YOUR_STUDY_ID>` and paste:

```powershell
$studyId = "<YOUR_STUDY_ID>"

pxc simulation list `
  --studyId $studyId `
  --orderBy CreatedAt `
  --descending `
  --top 10 `
  --format json
```

Choose a recent successful simulation that is:

* single-model;
* fast;
* known to produce Parquet output.

Copy its simulation ID.

## 10. Build an enqueue request from that simulation

Submitting simulations to PLEXOS Cloud can be done via JSON requests.

In PowerShell, replace the two placeholders below:

```powershell
$priorSimulationId = "<SIMULATION_ID_YOU_SELECTED>"

$requestFolder = `
  "<LOCAL_FOLDER_WHERE_YOU_WANT_THE_REQUEST>"

New-Item `
  -ItemType Directory `
  -Force `
  -Path $requestFolder | Out-Null

pxc simulation build-request-from-previous `
  --simulationId $priorSimulationId `
  --outputDirectory $requestFolder `
  --file "plexos-s3-export-request.json" `
  --overwrite
```

You should now have:

```text
plexos-s3-export-request.json
```

Open that file in a text editor.

This is the request we will modify.

# Part 5 — Add the Linux post-simulation tasks

Skip to Appendix B for a bulk copy-paste able snippet with all the simulation tasks.

The tested Linux POC used eight tasks because I was deliberately proving several assumptions about the task environment.

Conceptually, they were:

```text
1. Validate Parquet output
2. Create shared symlink
3. Verify the link isn't dangling
4. Show where it points
5. Prove a later task can read through it
6. Create S3 connector
7. Upload Parquets
8. Delete connector
```

Tasks 3–5 are mostly diagnostic.

The operational pattern is simpler:

```text
Validate output
    ↓
Create shared link
    ↓
Create connector
    ↓
Upload
    ↓
Delete connector
```

For a first reproducible run, however, I recommend retaining the diagnostics. They make failures much easier to understand and reproduce the version I actually tested.

## 11. Understand the shared-link trick

PLEXOS Cloud injected a `solution_path` environment variable into the post-task environment.

In my test it looked like:

```text
/simulation/Model SnowflakeTest Solution
```

The spaces matter.

The Linux expression:

```bash
${solution_path// /?}
```

replaces each space with the Bash filename wildcard `?`.

That lets pathname expansion resolve the actual solution directory without embedding a model-specific name in the task.

The tested Parquet location was:

```text
${solution_path// /?}/version2/ParquetUploads
```

The second task creates:

```text
/output/parquet-source-linux
```

as a symbolic link to that directory.

The useful discovery was that `/output` is shared across the isolated post tasks. The symlink created by one task was therefore still available to later tasks.

# Part 6 — Configure the eight tested post tasks

The complete sanitized request is included in the appendix below, but the important task commands are worth seeing separately.

Use the **same unique connector name** in Tasks 6, 7, and 8.

For example:

```text
PLEXOS_S3_EXPORT_20260923
```

## Task 1 — Validate required Parquet output

```bash
ls ${solution_path// /?}/version2/ParquetUploads/{fullkeyinfo/FullKeyInfo.parquet,period/Period.parquet,data/dataFileId=*/*.parquet}
```

This is simply a sanity check that the expected solution output exists.

## Task 2 — Create a shared symlink

```bash
ln -sT -- ${solution_path// /?}/version2/ParquetUploads /output/parquet-source-linux
```

The remainder of the workflow can now refer to:

```text
/output/parquet-source-linux
```

instead of the original simulation path.

## Task 3 — Verify the link resolves

```bash
test -d /output/parquet-source-linux
```

## Task 4 — Show the target

```bash
readlink /output/parquet-source-linux
```

The post-simulation log will now tell you which actual solution directory was selected.

## Task 5 — Prove a later task can read through the link

```bash
ls /output/parquet-source-linux/fullkeyinfo/FullKeyInfo.parquet
```

This was important during development because the post tasks run separately. It proves that a later task can still follow the link created by Task 2.

## Task 6 — Create the S3 connector

Replace:

```text
<CONNECTOR_NAME>
<AWS_REGION>
<S3_BUCKET_NAME>
```

with your values:

```bash
plexos-cloud datahub connector create --name <CONNECTOR_NAME> --connector-type AmazonS3 --auth-type AccountCreds --s3-access-key $S3_ACCESS_KEY --s3-secret-key $S3_SECRET_KEY --region <AWS_REGION> --bucket-name <S3_BUCKET_NAME> --format json --quiet
```

This task receives the two PLEXOS Cloud secrets created earlier as:

```text
S3_ACCESS_KEY
S3_SECRET_KEY
```

## Task 7 — Upload all Parquets

Use the **same connector name**:

```bash
plexos-cloud datahub upload --local-folder /output/parquet-source-linux --remote-folder connectors/AmazonS3/<CONNECTOR_NAME>/plexos/solutions/$simulation_id --pattern \*\*/\*.parquet --is-versioned false --parallel-upload false --format json
```

The destination automatically uses the current PLEXOS Cloud:

```text
$simulation_id
```

so each run gets its own S3 folder.

## Task 8 — Delete the connector

Again, use the same connector name:

```bash
plexos-cloud datahub connector delete --name <CONNECTOR_NAME> --format json --quiet
```

# Part 7 — Enqueue the modified simulation

## 12. Submit the request

After adding the tasks to the request JSON and saving it, open PowerShell.

Set `$requestFile` to the actual file you edited:

```powershell
$requestFile = `
  "<ABSOLUTE_PATH_TO_YOUR_plexos-s3-export-request.json>"
```

Then enqueue it:

```powershell
pxc simulation enqueue `
  --file $requestFile `
  --format json `
  --quiet
```

The response contains the new simulationId. 
Copy that value.
You will need it in the next step.

# Part 8 — Inspect the result

## 13. Set the new simulation ID

Up to this point, you can simply confirm in the S3 bucket whether this worked or not.
The remaining instructions guide you through the process of inspecting the post-simulation task outputs.

In the **same or a new PowerShell window**, paste your returned ID here:

```powershell
$simulationId = "<NEW_SIMULATION_ID_FROM_ENQUEUE>"
```

Then run:

```powershell
pxc simulation progress `
  --simulationId $simulationId `
  --format json `
  --quiet
```

Wait until the simulation has produced its solution before trying to retrieve the post-simulation log.

## 14. Find the AgentLog solution

Once the solution is available, copy and paste this entire block:

```powershell
$solutions = `
  pxc solution list `
    --simulationId $simulationId `
    --format json `
    --quiet |
  ConvertFrom-Json

$solutionId = (
  $solutions |
  Where-Object Type -eq "AgentLog" |
  Select-Object -First 1
).SolutionId

if (-not $solutionId) {
  throw "No AgentLog solution ID is available yet."
}

Write-Host "AgentLog solution ID: $solutionId"
```

If this returns:

```text
No AgentLog solution ID is available yet.
```

wait for the simulation to progress further and run the block again.

## 15. Download the post-simulation log

Once `$solutionId` has a value, copy and paste:

```powershell
$downloadTo = `
  Join-Path $env:TEMP "plexos-post-task-$simulationId"

New-Item `
  -ItemType Directory `
  -Force `
  -Path $downloadTo | Out-Null

pxc solution files download `
  --solutionId $solutionId `
  --type AgentLog `
  --file Post_Simulation.log `
  --outputDirectory $downloadTo `
  --overwrite `
  --quiet

$postLog = `
  Join-Path $downloadTo "Post_Simulation.log"

Get-Content -LiteralPath $postLog
```

You should see each post-simulation task and its exit code.

In my tested run, all eight tasks exited with:

```text
Exit Code: 0
```

and the upload task logged 21 lines beginning with:

```text
Uploading SUCCESS
```

The exact number of Parquet files will depend on the solution.

# Part 9 — Verify S3

## 16. Find the exported solution

For a simulation ID of:

```text
<NEW_SIMULATION_ID>
```

the DataHub destination is:

```text
connectors/AmazonS3/<CONNECTOR_NAME>/plexos/solutions/<NEW_SIMULATION_ID>
```

but the physical S3 location is:

```text
s3://<S3_BUCKET_NAME>/plexos/solutions/<NEW_SIMULATION_ID>/
```

The nested Parquet directory structure should be retained.

Examples from my test included:

```text
fullkeyinfo/FullKeyInfo.parquet
period/Period.parquet
data/dataFileId=0/<solution-id>_data_0.parquet
```

At this point the integration has worked.

# Troubleshooting notes I wish I'd had earlier

## Connector creation reports invalid credentials or insufficient permissions

Check:

* AWS access key;
* AWS secret key;
* bucket name;
* AWS Region;
* IAM bucket permissions;
* IAM object permissions.

In particular, remember the staging prefix:

```text
energyexemplar_temp_uploads/*
```

## Upload reports that versioned resources are not supported

The upload command needs:

```text
--is-versioned false
```

## The upload succeeds but I can't find `connectors/AmazonS3/...` in S3

That's expected.

This:

```text
connectors/AmazonS3/<connector-name>/
```

belongs to DataHub's logical path.

Instead, look at the bucket root under:

```text
plexos/solutions/
```

## The Linux command fails around the solution path

The tested simulation path contained spaces.

The Linux POC handled those spaces using:

```bash
${solution_path// /?}
```

This approach assumes one matching single-model solution directory and the observed layout:

```text
version2/ParquetUploads
```

The more robust Python-based approach I tested separately reads PLEXOS Cloud's directory mapping rather than inferring this path. That's preferable if these assumptions no longer hold.

## The symlink is created but a later task can't use it

The tested POC explicitly checked this with:

```bash
test -d /output/parquet-source-linux
```

and:

```bash
ls /output/parquet-source-linux/fullkeyinfo/FullKeyInfo.parquet
```

In the tested environment, `/output` and `/simulation` appeared at the same absolute paths across the isolated post-task containers, allowing the symlink in shared `/output` to survive between tasks.

## A failed run leaves the connector behind

List the existing connectors:

```powershell
pxc datahub connector list --format json
```

Identify the temporary connector from that run and delete it:

```powershell
pxc datahub connector delete `
  --name "<CONNECTOR_NAME>"
```

# What I would simplify after proving it works

The eight-task version is useful as a capability test because it leaves evidence for each assumption.

Once the workflow is established, Tasks 3–5 are diagnostic rather than fundamental.

The essential pattern is:

```text
1. Validate Parquet output
2. Create /output symlink
3. Create S3 connector
4. Upload through symlink
5. Delete connector
```

I would keep the verbose version around as the reproducible reference and simplify only after I had a reason to.

# Final takeaway

The most useful lesson for future me is:

> **Prove the DataHub → S3 connection with one harmless file before debugging anything involving a simulation.**

Once that works, the PLEXOS side is:

```text
fast known-good simulation
        ↓
ParquetUploads
        ↓
shared /output symlink
        ↓
temporary DataHub connector
        ↓
S3
```

The PLEXOS Cloud secrets bridge the AWS credentials into the post-task environment, `$simulation_id` gives each run a natural destination, and the temporary connector can disappear when the upload is complete.

Simple in retrospect. Less simple the first time.

---

# Appendix A — Anatomy of the post-task configuration

The eight post tasks belong in:

```text
SimulationOptions.SimulationTasks
```

of the simulation enqueue request.

A sanitized version of the tested task array looks like this:

```json
[
  {
    "Name": "Validate Linux Parquet source",
    "TaskType": "Post",
    "Files": [],
    "Arguments": "ls ${solution_path// /?}/version2/ParquetUploads/{fullkeyinfo/FullKeyInfo.parquet,period/Period.parquet,data/dataFileId=*/*.parquet}",
    "ContinueOnError": true,
    "ExecutionOrder": 1,
    "AppliesTo": [],
    "Secrets": []
  },
  {
    "Name": "Create Linux symlink for Parquet folder",
    "TaskType": "Post",
    "Files": [],
    "Arguments": "ln -sT -- ${solution_path// /?}/version2/ParquetUploads /output/parquet-source-linux",
    "ContinueOnError": true,
    "ExecutionOrder": 2,
    "AppliesTo": [],
    "Secrets": []
  },
  {
    "Name": "Validate Linux symlink",
    "TaskType": "Post",
    "Files": [],
    "Arguments": "test -d /output/parquet-source-linux",
    "ContinueOnError": true,
    "ExecutionOrder": 3,
    "AppliesTo": [],
    "Secrets": []
  },
  {
    "Name": "Show Linux symlink target",
    "TaskType": "Post",
    "Files": [],
    "Arguments": "readlink /output/parquet-source-linux",
    "ContinueOnError": true,
    "ExecutionOrder": 4,
    "AppliesTo": [],
    "Secrets": []
  },
  {
    "Name": "Read Parquet through Linux symlink",
    "TaskType": "Post",
    "Files": [],
    "Arguments": "ls /output/parquet-source-linux/fullkeyinfo/FullKeyInfo.parquet",
    "ContinueOnError": true,
    "ExecutionOrder": 5,
    "AppliesTo": [],
    "Secrets": []
  },
  {
    "Name": "Create temporary S3 connector",
    "TaskType": "Post",
    "Files": [],
    "Arguments": "plexos-cloud datahub connector create --name <CONNECTOR_NAME> --connector-type AmazonS3 --auth-type AccountCreds --s3-access-key $S3_ACCESS_KEY --s3-secret-key $S3_SECRET_KEY --region <AWS_REGION> --bucket-name <S3_BUCKET_NAME> --format json --quiet",
    "ContinueOnError": true,
    "ExecutionOrder": 6,
    "AppliesTo": [],
    "Secrets": [
      {
        "SecretKey": "S3-access-key-post",
        "VariableName": "S3_ACCESS_KEY"
      },
      {
        "SecretKey": "S3-secret-key-post",
        "VariableName": "S3_SECRET_KEY"
      }
    ]
  },
  {
    "Name": "Upload Parquets through Linux symlink",
    "TaskType": "Post",
    "Files": [],
    "Arguments": "plexos-cloud datahub upload --local-folder /output/parquet-source-linux --remote-folder connectors/AmazonS3/<CONNECTOR_NAME>/plexos/solutions/$simulation_id --pattern \\*\\*/\\*.parquet --is-versioned false --parallel-upload false --format json",
    "ContinueOnError": true,
    "ExecutionOrder": 7,
    "AppliesTo": [],
    "Secrets": []
  },
  {
    "Name": "Delete temporary S3 connector",
    "TaskType": "Post",
    "Files": [],
    "Arguments": "plexos-cloud datahub connector delete --name <CONNECTOR_NAME> --format json --quiet",
    "ContinueOnError": true,
    "ExecutionOrder": 8,
    "AppliesTo": [],
    "Secrets": []
  }
]
```

`ContinueOnError: true` was intentional in the capability test: I wanted later diagnostics—and especially cleanup—to have a chance to execute even if an earlier probe failed.

It also means that the overall simulation status alone is not enough to decide whether the integration worked. Inspect `Post_Simulation.log` and the S3 result.

For a production workflow, failure and cleanup behavior should be reconsidered rather than copying that setting automatically.

# Appendix B — Example enqueue request

The safest way to create a request remains:

```text
known-good simulation
        ↓
pxc simulation build-request-from-previous
        ↓
add SimulationTasks
```

rather than constructing the entire contract manually.

Still, it is useful to have a complete example showing where everything belongs.

The structure below is deliberately filled with placeholders. Values such as the study, change set, model, engine, resources, and simulation data should come from the fast known-good simulation being cloned.

```json
{
  "StudyId": "<STUDY_ID>",
  "ChangeSetId": "<CHANGE_SET_ID>",
  "Models": [
    "<MODEL_NAME>"
  ],
  "SimulationOptions": {
    "SimulationTasks": [
      {
        "Name": "Validate Linux Parquet source",
        "TaskType": "Post",
        "Files": [],
        "Arguments": "ls ${solution_path// /?}/version2/ParquetUploads/{fullkeyinfo/FullKeyInfo.parquet,period/Period.parquet,data/dataFileId=*/*.parquet}",
        "ContinueOnError": true,
        "ExecutionOrder": 1,
        "AppliesTo": [],
        "Secrets": []
      },
      {
        "Name": "Create Linux symlink for Parquet folder",
        "TaskType": "Post",
        "Files": [],
        "Arguments": "ln -sT -- ${solution_path// /?}/version2/ParquetUploads /output/parquet-source-linux",
        "ContinueOnError": true,
        "ExecutionOrder": 2,
        "AppliesTo": [],
        "Secrets": []
      },
      {
        "Name": "Validate Linux symlink",
        "TaskType": "Post",
        "Files": [],
        "Arguments": "test -d /output/parquet-source-linux",
        "ContinueOnError": true,
        "ExecutionOrder": 3,
        "AppliesTo": [],
        "Secrets": []
      },
      {
        "Name": "Show Linux symlink target",
        "TaskType": "Post",
        "Files": [],
        "Arguments": "readlink /output/parquet-source-linux",
        "ContinueOnError": true,
        "ExecutionOrder": 4,
        "AppliesTo": [],
        "Secrets": []
      },
      {
        "Name": "Read Parquet through Linux symlink",
        "TaskType": "Post",
        "Files": [],
        "Arguments": "ls /output/parquet-source-linux/fullkeyinfo/FullKeyInfo.parquet",
        "ContinueOnError": true,
        "ExecutionOrder": 5,
        "AppliesTo": [],
        "Secrets": []
      },
      {
        "Name": "Create temporary S3 connector",
        "TaskType": "Post",
        "Files": [],
        "Arguments": "plexos-cloud datahub connector create --name <CONNECTOR_NAME> --connector-type AmazonS3 --auth-type AccountCreds --s3-access-key $S3_ACCESS_KEY --s3-secret-key $S3_SECRET_KEY --region <AWS_REGION> --bucket-name <S3_BUCKET_NAME> --format json --quiet",
        "ContinueOnError": true,
        "ExecutionOrder": 6,
        "AppliesTo": [],
        "Secrets": [
          {
            "SecretKey": "S3-access-key-post",
            "VariableName": "S3_ACCESS_KEY"
          },
          {
            "SecretKey": "S3-secret-key-post",
            "VariableName": "S3_SECRET_KEY"
          }
        ]
      },
      {
        "Name": "Upload Parquets through Linux symlink",
        "TaskType": "Post",
        "Files": [],
        "Arguments": "plexos-cloud datahub upload --local-folder /output/parquet-source-linux --remote-folder connectors/AmazonS3/<CONNECTOR_NAME>/plexos/solutions/$simulation_id --pattern \\*\\*/\\*.parquet --is-versioned false --parallel-upload false --format json",
        "ContinueOnError": true,
        "ExecutionOrder": 7,
        "AppliesTo": [],
        "Secrets": []
      },
      {
        "Name": "Delete temporary S3 connector",
        "TaskType": "Post",
        "Files": [],
        "Arguments": "plexos-cloud datahub connector delete --name <CONNECTOR_NAME> --format json --quiet",
        "ContinueOnError": true,
        "ExecutionOrder": 8,
        "AppliesTo": [],
        "Secrets": []
      }
    ],
    "SolutionOptions": {
      "ParquetSchemaVersion": 2
    },
    "EnableRealTimeLog": true
  },
  "SimulationData": [
    {
      "Uri": "<INPUT_DATA_URI>",
      "Type": 0
    },
    {
      "Uri": "<TIMESERIES_DATA_URI>",
      "Type": 4
    }
  ],
  "SimulationEngine": {
    "EngineId": "<ENGINE_ID>",
    "Version": "<ENGINE_VERSION>",
    "Name": "<ENGINE_NAME>",
    "EngineType": "<ENGINE_TYPE>"
  },
  "Source": "CloudCLI",
  "Priority": 1,
  "RequestedCpuCores": <CPU_CORES>,
  "MinimumMemoryInGb": <MEMORY_GB>
}
```

Treat that as a map of the request rather than a substitute for cloning a valid request. The PLEXOS Cloud request contract contains additional fields depending on the simulation configuration.

The part this Note is really adding is:

```text
SimulationOptions.SimulationTasks
```

Everything else should preferably come from the simulation you already know works.
