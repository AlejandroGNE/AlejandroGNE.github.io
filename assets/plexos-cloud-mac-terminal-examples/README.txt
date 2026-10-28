PLEXOS from Mac: Terminal Examples — supporting files

Extract this archive into workspace/terminal-examples/helpers in the terminal
starter. Follow the article in one Mac Terminal window. Its PLEXOS variable holds
the absolute path to the launcher; CLI paths beginning /workspace refer to the
starter's workspace folder inside Linux.

Files
  query.py          Inspect local metadata, generate SQL, run it locally,
                    and compare local/remote CSVs. No network calls.
  bundle-tail.sql   SQL for the count, ordered values and summary rows.
  requirements.txt  DuckDB 1.4.5, matching the tested local environment.

Requirements and use
  Python 3.9+ on the Mac. Run query.py --help or any subcommand with --help.
  Keep the complete downloaded Parquet folder structure for your first query.
  The helper supports the tested layout: FullKeyInfo, Period and partitioned
  data/dataFileId=... files. It does not support every PLEXOS format.
  Only execute trusted SQL: the local command passes SQL directly to DuckDB.
  Local output files must not exist. Choose a new output name for repeat runs.
  No PLEXOS Python SDK is needed. The remote command uses the authenticated CLI.

Choosing and interpreting a result
  KeyId selects exactly one metadata row. Confirm model, phase, object, property,
  units, period type, sample, band and timeslice before generating the SQL.
  The inspection's date ranges describe each period type, not guaranteed data
  coverage for every key. Check the query's count and dates after execution.
  Start/end filters apply to period StartDate inclusively, without timezone
  conversion. The SQL uses DataFileId plus SeriesId and the selected KeyId;
  PeriodId joins also compare nullable EpochId and match PeriodTypeId.
  The output contains a completeness row, time_series rows ordered by date and
  period ID, and an aggregate row with minimum, maximum, first and last values.
  Check RowCount > 0, expected NonNullCount, and DistinctPeriods = RowCount.
  These examples do not average prices, total energy or infer duration weights.

Comparison details
  Column names are compared case-insensitively. Row order must agree.
  Blank and 'null' fields represent null; timestamps are parsed as ISO dates.
  Finite numeric values use abs=1e-8, rel=1e-9. Counts/IDs in these examples fit
  exactly in a double; adapt the comparison for unusually large integer IDs.
  A match checks only this query/selection, not all properties or model inputs.

CLI notes for scripts
  Model logs in the tested solution are listed/downloaded with --type Log.
  CLI 1.5.2981 supports solution query sql --solution-id ... --sql-file ...
  --output-file ... . SQL files must be under 1 MB and begin with SELECT or WITH.
  The remote output path is overwritten if it already exists.
  The tested remote mechanism submitted an HTTP POST SQL request to the solution
  service. No claim is made about enabled streaming features or server caching.
  File listings reported filename and size, not independent file timestamps.
  Paginate by the number of records actually returned: a request for 1,000
  solution records returned at most 250 in the retained test. An exhausted page
  returned empty stdout and a no-records notice on stderr with exit status 0.
  Retain both output channels. Some CLI responses include prose around JSON.

Download recovery
  Existing files do not mean a bulk download will skip or resume them.
  Compare local sizes with FileSizeBytes. Retain completed files; move incomplete
  ones aside and retry only missing/incomplete filenames into the original
  destination. This restarts a file, not a tested byte-range resume.
  A local SHA-256 is useful for later integrity checks but is not a comparison
  with a server checksum unless that checksum was independently provided.
  Keep CLI state and credentials private; run serially with the terminal starter.
