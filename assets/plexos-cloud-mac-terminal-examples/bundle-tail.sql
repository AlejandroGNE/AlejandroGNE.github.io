SELECT 'completeness' Kind,0::BIGINT Ordinal,NULL::INTEGER PeriodId,MIN(StartDate) StartDate,MAX(EndDate) EndDate,
 NULL::DOUBLE AS "Value",COUNT(*) RowCount,COUNT(Value) NonNullCount,COUNT(DISTINCT PeriodId) DistinctPeriods,
 NULL::DOUBLE Minimum,NULL::DOUBLE Maximum,NULL::DOUBLE FirstValue,NULL::DOUBLE LastValue FROM s
 UNION ALL
 SELECT 'time_series',ROW_NUMBER() OVER(ORDER BY StartDate,PeriodId),PeriodId,StartDate,EndDate,Value,
 NULL,NULL,NULL,NULL,NULL,NULL,NULL FROM s
 UNION ALL
 SELECT 'aggregate',2147483647,NULL,NULL,NULL,NULL,NULL,NULL,NULL,MIN(Value),MAX(Value),
 (SELECT Value FROM s ORDER BY StartDate,PeriodId LIMIT 1),
 (SELECT Value FROM s ORDER BY StartDate DESC,PeriodId DESC LIMIT 1) FROM s
 ORDER BY Ordinal;
