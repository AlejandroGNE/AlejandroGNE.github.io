"""Small local Parquet / equivalent remote-CSV example. No network calls."""
import argparse
import csv
import datetime as dt
import math
from pathlib import Path


def connect(folder):
    import duckdb
    con = duckdb.connect()
    con.execute("SET threads=2")
    con.execute("SET memory_limit='2GB'")
    names = set()
    for file in sorted(folder.rglob('*.parquet')):
        if file.is_relative_to(folder / 'data'):
            continue
        name = file.stem.lower()
        if name in names:
            raise ValueError(f'Duplicate metadata view: {name}')
        names.add(name)
        identifier = '"' + name.replace('"', '""') + '"'
        path = str(file).replace("'", "''")
        con.execute(f"CREATE VIEW {identifier} AS SELECT * FROM read_parquet('{path}')")
    pattern = str(folder / 'data/**/*.parquet').replace("'", "''")
    con.execute(f"CREATE VIEW data AS SELECT * FROM read_parquet('{pattern}', hive_partitioning=true)")
    return con


def write_csv(cursor, path):
    with path.open('x', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([c[0] for c in cursor.description])
        writer.writerows(cursor.fetchall())


def compare(left, right):
    def read(path):
        with path.open(encoding='utf-8-sig', newline='') as file:
            rows = list(csv.reader(file))
        return [v.lower() for v in rows[0]], rows[1:]
    h1, a = read(left)
    h2, b = read(right)
    if h1 != h2 or len(a) != len(b):
        raise ValueError('Different columns or row counts')
    numeric = {'ordinal', 'periodid', 'value', 'rowcount', 'nonnullcount',
               'distinctperiods', 'minimum', 'maximum', 'firstvalue', 'lastvalue'}
    max_diff = 0.0
    for n, (x, y) in enumerate(zip(a, b), 1):
        if len(x) != len(h1) or len(y) != len(h1):
            raise ValueError(f'Malformed CSV row {n}')
        for col, v, w in zip(h1, x, y):
            v, w = v.strip(), w.strip()
            if v.lower() in ('', 'null') and w.lower() in ('', 'null'):
                continue
            if col in numeric:
                f, g = float(v), float(w)
                ok = math.isfinite(f) and math.isfinite(g) and math.isclose(f, g, abs_tol=1e-8, rel_tol=1e-9)
                if ok:
                    max_diff = max(max_diff, abs(f-g))
            elif col in ('startdate', 'enddate'):
                ok = dt.datetime.fromisoformat(v.replace('Z', '+00:00')) == dt.datetime.fromisoformat(w.replace('Z', '+00:00'))
            else:
                ok = v == w
            if not ok:
                raise ValueError(f'Mismatch at row {n}, column {col}')
    print(f'MATCH: {len(a)} rows; maximum absolute numeric difference {max_diff:g}; abs=1e-8, rel=1e-9')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('inspect', 'make-query', 'local'):
        p = sub.add_parser(name)
        p.add_argument('--solution-dir', type=Path, required=True)
        p.add_argument('--output', type=Path, required=True)
        if name == 'make-query':
            p.add_argument('--key-id', type=int, required=True)
            p.add_argument('--start', required=True)
            p.add_argument('--end', required=True)
        if name == 'local':
            p.add_argument('--sql', type=Path, required=True)
    p = sub.add_parser('compare')
    p.add_argument('local', type=Path)
    p.add_argument('remote', type=Path)
    args = parser.parse_args()
    if args.command == 'compare':
        compare(args.local, args.remote)
        return
    if args.output.exists():
        raise ValueError('Output already exists; choose a new name')
    con = connect(args.solution_dir.resolve())
    try:
        if args.command == 'inspect':
            write_csv(con.execute('SELECT * FROM fullkeyinfo ORDER BY KeyId'), args.output)
            print('Review the metadata CSV before choosing a KeyId. Available calendar bounds:')
            bounds = con.execute('''SELECT k.PeriodTypeName, MIN(p.StartDate), MAX(p.StartDate)
                FROM period p JOIN (SELECT DISTINCT PeriodTypeId, PeriodTypeName FROM fullkeyinfo) k
                ON p.PeriodTypeId=k.PeriodTypeId GROUP BY k.PeriodTypeName ORDER BY k.PeriodTypeName''').fetchall()
            for name, first, last in bounds:
                print(f'{name}: {first} through {last}')
        elif args.command == 'local':
            write_csv(con.execute(args.sql.read_text()), args.output)
        else:
            lo, hi = dt.datetime.fromisoformat(args.start), dt.datetime.fromisoformat(args.end)
            if lo.tzinfo or hi.tzinfo or lo > hi:
                raise ValueError('Use ordered naive model-calendar start dates, without a timezone')
            cur = con.execute('SELECT * FROM fullkeyinfo WHERE KeyId=?', [args.key_id])
            rows = cur.fetchall()
            if len(rows) != 1:
                raise ValueError('KeyId must identify exactly one semantic key')
            key = dict(zip([c[0] for c in cur.description], rows[0]))
            print('Selected key (check model, phase, property, object, units, sample, band and timeslice):')
            print(key)
            quote = lambda x: "'" + str(x).replace("'", "''") + "'"
            core = f'''SELECT d.PeriodId,p.StartDate,p.EndDate,d.Value
FROM data d JOIN fullkeyinfo k ON d.SeriesId=k.SeriesId AND d.dataFileId=k.DataFileId
JOIN period p ON p.PeriodId=d.PeriodId AND p.EpochId IS NOT DISTINCT FROM d.EpochId
WHERE d.SeriesId={int(key['SeriesId'])} AND d.dataFileId={int(key['DataFileId'])}
AND k.KeyId={args.key_id} AND k.ModelName={quote(key['ModelName'])} AND k.PhaseName={quote(key['PhaseName'])}
AND p.PeriodTypeId=k.PeriodTypeId
AND p.StartDate BETWEEN TIMESTAMP {quote(lo)} AND TIMESTAMP {quote(hi)}'''
            tail = Path(__file__).with_name('bundle-tail.sql').read_text()
            with args.output.open('x') as file:
                file.write('WITH s AS (\n' + core + '\n)\n' + tail)
            print('SQL written; dates filter period StartDate inclusively. Check nonzero, unique period counts.')
    finally:
        con.close()


if __name__ == '__main__':
    main()
