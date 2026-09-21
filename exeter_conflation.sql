.headers on
.mode column

SELECT '=== 1. Conflation Status Distribution ===' AS section;

SELECT
    matchStatus,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM roadlinks), 2) AS percent
FROM roadlinks
GROUP BY matchStatus
ORDER BY count DESC;

SELECT '=== 2a. Unmatched by roadClassification ===' AS section;

SELECT roadClassification, COUNT(*) AS count
FROM roadlinks
WHERE matchStatus = 'No Match'
GROUP BY roadClassification
ORDER BY count DESC;

SELECT '=== 2b. Unmatched by formOfWay ===' AS section;

SELECT formOfWay, COUNT(*) AS count
FROM roadlinks
WHERE matchStatus = 'No Match'
GROUP BY formOfWay
ORDER BY count DESC;

SELECT '=== 2c. Unmatched by provenance ===' AS section;

SELECT provenance, COUNT(*) AS count
FROM roadlinks
WHERE matchStatus = 'No Match'
GROUP BY provenance
ORDER BY count DESC;

SELECT '=== 3. Length statistics of unmatched ===' AS section;

SELECT
    COUNT(*) AS count,
    ROUND(MIN(length), 2) AS min_length,
    ROUND(AVG(length), 2) AS mean_length,
    ROUND(MAX(length), 2) AS max_length
FROM roadlinks
WHERE matchStatus = 'No Match';

SELECT '=== 4. Top 10 longest unmatched ===' AS section;

SELECT roadName, roadClassification, formOfWay, ROUND(length, 2) AS length
FROM roadlinks
WHERE matchStatus = 'No Match'
ORDER BY length DESC
LIMIT 10;

SELECT '=== 5. Unmatched classified roads ===' AS section;

SELECT roadName, roadClassification, ROUND(length, 2) AS length
FROM roadlinks
WHERE matchStatus = 'No Match'
  AND roadClassification IN ('A Road', 'B Road', 'Motorway')
ORDER BY length;

SELECT '=== 6. Attribute discrepancies by road name ===' AS section;

SELECT roadName, COUNT(*) AS count
FROM roadlinks
WHERE matchStatus = 'Matched With Attribute Discrepancy'
GROUP BY roadName
ORDER BY count DESC;

SELECT '=== 7. Matched baseline by classification ===' AS section;

SELECT roadClassification, COUNT(*) AS count
FROM roadlinks
WHERE matchStatus = 'Matched'
GROUP BY roadClassification
ORDER BY count DESC;

SELECT '=== 8. Cross-table check: streets vs roadlinks ===' AS section;

SELECT 'streets' AS table_name, COUNT(*) AS row_count FROM streets
UNION ALL
SELECT 'roadlinks', COUNT(*) FROM roadlinks;
