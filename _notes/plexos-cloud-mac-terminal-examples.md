---
title: "PLEXOS from Mac: Terminal Examples"
date: 2026-10-27
description: "Find a completed simulation, download its results, and compare the same query on your Mac and in PLEXOS Cloud."
---

After setting up the [terminal workspace](/notes/plexos-cloud-mac-terminal-setup/), you can use it to find a study, download results, and run a query. This note follows one completed simulation and compares the same results on your Mac and in PLEXOS Cloud.

Start with a **small completed simulation** that you can access. You will need its Parquet results, which are the data files used for the local query. If the download is large, choose a smaller example for your first attempt.

Three identifiers appear along the way:

| Identifier | What it identifies |
|---|---|
| Study ID | The study containing your model inputs. |
| Simulation ID | A run of one or more models. |
| Solution ID | Results produced for a model in a run. |

Copy each ID from the corresponding command output. They are not interchangeable.

The excerpts below come from actual command runs. Private names, IDs, dates and paths are replaced with placeholders; `…` marks omitted output. Your values will differ.

## 1. Open the workspace

Start Docker Desktop. In **Mac Terminal**, run:

```bash
cd "$HOME/Documents/plexos-from-mac"
PLEXOS="$PWD/plexos"
"$PLEXOS" check

mkdir -p workspace/terminal-examples
cd workspace/terminal-examples
```

Keep this Terminal window open for the rest of the note. `PLEXOS` stores the launcher's location, so you can run it from the results folder. The launcher runs the CLI inside Linux automatically; you do not need to open a Linux shell.

Look for `Authenticated` and the final readiness message:

```text
PLEXOS Cloud CLI
1.5.2981
Status: Authenticated, Environment: NA, Tenant: <TENANT_NAME>.
CLI readiness check passed.
```

If the check asks you to authenticate, run `"$PLEXOS" login`, then repeat `"$PLEXOS" check`. Run one CLI command at a time to avoid competing operations on the saved session.

## 2. Find your study and simulation

List 15 recently updated studies:

```bash
"$PLEXOS" study list --orderBy LastUpdatedAtUtc --descending \
  --top 15 --format json
```

A cropped study record:

```text
    "Id": "<STUDY_ID>",
    "Name": "<STUDY_NAME>",
    …
    "Status": "Active",
```

Find your study's name and copy its `Id`. Replace `YOUR_STUDY_ID` below, keeping the quotes:

```bash
STUDY_ID='YOUR_STUDY_ID'
"$PLEXOS" simulation list --studyId "$STUDY_ID" \
  --orderBy CreatedAt --descending --top 15 --format json
```

Look for the simulation `Id`, the model names, and a successful status (other fields omitted):

```text
    "Id": "<SIMULATION_ID>",
    …
    "Models": [
      "<MODEL_NAME>"
    ],
    "Status": "CompletedSuccess",
```

Choose a simulation whose `Status` is `CompletedSuccess` and copy its `Id`. If the run you need is older, add `--skip 15` to see the next page. These lists are recent overviews, not the complete history.

## 3. Select a solution and list its files

Replace the simulation ID and run:

```bash
SIMULATION_ID='YOUR_SIMULATION_ID'
"$PLEXOS" solution list --simulationId "$SIMULATION_ID" \
  --type Parquet --status Complete \
  --orderBy CreatedDate --descending --top 15 --format json
```

Selected fields from the returned solution record:

```text
    "SolutionId": "<SOLUTION_ID>",
    …
    "SimulationId": "<SIMULATION_ID>",
    "Type": "Parquet",
    "Status": "Complete",
    …
    "ModelName": "<MODEL_NAME>",
```

Check `ModelName` and copy the corresponding `SolutionId`. One simulation can contain results for several models, so choose the model you want rather than the first row.

```bash
SOLUTION_ID='YOUR_SOLUTION_ID'
"$PLEXOS" solution files list --solutionId "$SOLUTION_ID" \
  --type Parquet --format json
```

Zooming in on one metadata file:

```text
        "FileName": "fullkeyinfo/FullKeyInfo.parquet",
        "FileSizeBytes": 35324
```

The output lists each `FileName` and `FileSizeBytes`. Check that you have enough disk space for the complete Parquet set before continuing:

```bash
df -h .
```

Read the `Avail` column. This was the available space on my Mac at the time:

```text
Filesystem      Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s5   228Gi   173Gi    20Gi    90%    1.0M  207M    0%   /System/Volumes/Data
```

The ordering above selects recent solution records. The file listing itself does not provide file creation dates.

## 4. Download the results

For this first query, download all Parquet files for the selected small solution. This includes the metadata needed to identify and interpret its values.

```bash
"$PLEXOS" solution files download --solutionId "$SOLUTION_ID" \
  --type Parquet \
  --outputDirectory "/workspace/terminal-examples/results/$SOLUTION_ID"
```

The tested download printed progress and a completion line (intermediate files omitted):

```text
Beginning download of 21 files
…
Downloaded 21 files to directory: <DOWNLOAD_DIRECTORY>
```

These download messages appeared on the terminal’s error-output channel, even though the command succeeded.

Use a new destination for the first download. Inside Linux, `/workspace` is the same folder as the starter's `workspace` folder on your Mac. Your files will appear under:

```text
Documents/plexos-from-mac/workspace/terminal-examples/results/
```

Keep the downloaded subfolders unchanged.

To download a model log, first list its exact filename:

```bash
"$PLEXOS" solution files list --solutionId "$SOLUTION_ID" \
  --type Log --format json
```

```text
    "SolutionType": "Log",
    …
        "FileName": "Model ( <MODEL_NAME> ) Log.txt",
```

Copy that filename, including its spaces:

```bash
LOG_FILE='EXACT_FILENAME_FROM_THE_LIST'
"$PLEXOS" solution files download --solutionId "$SOLUTION_ID" \
  --type Log --file "$LOG_FILE" \
  --outputDirectory "/workspace/terminal-examples/logs/$SOLUTION_ID"
```

The individual log download finished with:

```text
Downloaded 1 files to directory: <LOG_DIRECTORY>
```

You can also download a single Parquet file with `--file`:

```bash
PARQUET_FILE='EXACT_RELATIVE_FILENAME_FROM_THE_LIST'
"$PLEXOS" solution files download --solutionId "$SOLUTION_ID" \
  --type Parquet --file "$PARQUET_FILE" \
  --outputDirectory "/workspace/terminal-examples/selected-files/$SOLUTION_ID"
```

For my single-file test, I selected `fullkeyinfo/FullKeyInfo.parquet`:

```text
Beginning download of 1 files
…
Saving file: fullkeyinfo/FullKeyInfo.parquet
```

This last command is optional and uses a separate folder. A single data file is generally insufficient for the query below; use the complete set in `results` for that example.

**If a download stops:** do not restart the bulk command blindly. This CLI release stops on existing files and may leave an incomplete file after a failed transfer. Compare the local file's size with `FileSizeBytes`:

```bash
PARQUET_FILE='EXACT_RELATIVE_FILENAME_FROM_THE_LIST'
stat -f '%z bytes' "results/$SOLUTION_ID/$PARQUET_FILE"
```

For the metadata file listed above, the size check returned:

```text
35324 bytes
```

Keep completed files. Move incomplete files aside and retry individual missing or incomplete files with `--file`, using the original `results` destination. The tested recovery restarts those files from the beginning.

## 5. Choose a result to query

[Download the example helpers](/assets/plexos-cloud-mac-terminal-examples/terminal-examples.zip) and save the ZIP in **Downloads**. In the same Mac Terminal window:

```bash
unzip -q "$HOME/Downloads/terminal-examples.zip" -d helpers
python3 -m venv query-env
query-env/bin/python -m pip install -r helpers/requirements.txt

query-env/bin/python helpers/query.py inspect \
  --solution-dir "results/$SOLUTION_ID" --output keys.csv
open keys.csv
```

This step requires Python 3.9 or newer on your Mac.

Creating the environment and extracting the ZIP normally finish without a message. The dependency installation in this run ended with:

```text
Successfully installed duckdb-1.4.5
```

DuckDB, installed by the command above, reads the local Parquet files. It does not require a PLEXOS Python SDK or a cloud login.

In `keys.csv`, choose one result—for example, a node's price or a region's generation capacity. Use these columns to identify it:

| Column | What to check |
|---|---|
| `ModelName` | The model you selected. |
| `PhaseName` | The simulation phase, such as short-term (`ST`) or long-term (`LT`). |
| `ChildObjectName`, `PropertyName`, `UnitValue` | The object, measurement and units you want. |
| `PeriodTypeName` | The time interval, such as an interval or a year. |
| `SampleName`, `BandId`, `TimesliceName` | The sample, band and timeslice you intend to compare. |
| `KeyId` | The integer to copy after checking the other columns. |

The inspection command also prints available dates for each period type. Choose dates within the selected result's calendar.

A cropped inspection output:

```text
Review the metadata CSV before choosing a KeyId. Available calendar bounds:
…
Year: <FIRST_DATE> through <LAST_DATE>
```

## 6. Query the downloaded results

Replace the key ID and example dates below with your selection:

```bash
KEY_ID='YOUR_INTEGER_KEY_ID'
START_DATE='2030-01-01 00:00:00'
END_DATE='2030-12-31 23:00:00'

query-env/bin/python helpers/query.py make-query \
  --solution-dir "results/$SOLUTION_ID" --key-id "$KEY_ID" \
  --start "$START_DATE" --end "$END_DATE" --output comparison.sql
```

After printing the selected metadata, the helper confirmed:

```text
Selected key (check model, phase, property, object, units, sample, band and timeslice):
…
SQL written; dates filter period StartDate inclusively. Check nonzero, unique period counts.
```

Run the generated query locally:

```bash
query-env/bin/python helpers/query.py local \
  --solution-dir "results/$SOLUTION_ID" \
  --sql comparison.sql --output local.csv
```

The local command completed without terminal output. Check the CSV’s header:

```bash
head -n 1 local.csv
```

```text
Kind,Ordinal,PeriodId,StartDate,EndDate,Value,RowCount,NonNullCount,DistinctPeriods,Minimum,Maximum,FirstValue,LastValue
```

The helper prints the selected result's details and writes `comparison.sql`. The dates select periods whose start dates fall within that range, including both endpoints. Dates come from the model's calendar; this example does not convert timezones.

Open `local.csv`. It contains a count of the values found, the values in date order, and a summary showing the minimum, maximum, first and last values. Check that the count is nonzero and that the dates cover the period you intended.

## 7. Run the same query in PLEXOS Cloud

Still in the same Mac Terminal window:

```bash
"$PLEXOS" solution query sql --solution-id "$SOLUTION_ID" \
  --sql-file /workspace/terminal-examples/comparison.sql \
  --output-file /workspace/terminal-examples/remote.csv
```

The remote command reported:

```text
Query executed successfully. Results exported to: /workspace/terminal-examples/remote.csv
```

Now compare the files:

```bash
query-env/bin/python helpers/query.py compare local.csv remote.csv
```

The actual comparison output was:

```text
MATCH: … rows; maximum absolute numeric difference 0; abs=1e-8, rel=1e-9
```

The row count is omitted here. The reported maximum difference was zero in this run.

The CLI sends the SQL query to the PLEXOS Cloud solution service and saves the returned results as `remote.csv`. The local query reads downloaded files; the remote query uses the same solution ID and SQL in the cloud. This example does not rely on streaming.

If the comparison prints `MATCH`, the two files agree within the helper's small rounding tolerance. If they differ, check the solution ID, downloaded files, selected result and date range first.

The local helper requires new output filenames. The remote CLI overwrites an existing `remote.csv`, so rename it before repeating a comparison you want to preserve.

## Optional: clone the study inputs

Cloning is useful if you also want to inspect the study's inputs. It is not required for the result queries above.

```bash
"$PLEXOS" study clone --studyId "$STUDY_ID" \
  --outputDirectory /workspace/terminal-examples/study-clone
```

The clone command confirmed the destination:

```text
Study saved to local path: /workspace/terminal-examples/study-clone
```

Use a new folder. This downloads a tracked local copy; it does not create a new study in PLEXOS Cloud.

## If something fails

| Symptom | What to check |
|---|---|
| Your run is missing | Look beyond the first page and confirm it completed successfully. |
| No output appears | Read the terminal's error messages too; some CLI messages use the error-output channel. |
| A download fails or reports an existing file | Keep completed files, move incomplete files aside, and retry individual files. |
| A local query reports missing files or tables | Check that the complete Parquet set is in `results`, with its original folders. |
| Login or license checks fail | Close competing CLI sessions and run `"$PLEXOS" check`. Preserve the saved state while investigating; do not delete it as a first step. |

For available options, append `--help` to a command, for example:

```bash
"$PLEXOS" solution files download --help
```

A cropped section of the installed help:

```text
  --solutionId          Filter by the solution ID (required)
  --file                Download specific file by name
```

These examples were tested with Toolkit 1.5.2981.559 / CLI 1.5.2981 and DuckDB 1.4.5, using the observed PLEXOS Parquet layout. Further details are in the helper's README and the official [CLI Toolkit guide](https://docs.energyexemplar.com/plexos-cloud/cli/cli-toolkit).
