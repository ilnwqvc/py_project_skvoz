-- 1
SELECT COUNT(*) FROM mart_variant_06;

-- 2
SELECT MIN(date), MAX(date) FROM mart_variant_06;

-- 3
SELECT * FROM mart_variant_06
WHERE date IS NULL OR city_id IS NULL;

-- 4
SELECT date, city_id, COUNT(*)
FROM mart_variant_06
GROUP BY date, city_id
HAVING COUNT(*) > 1;

-- 5
SELECT AVG("T_mean"), SUM("P_sum"), MAX(wind_max)
FROM mart_variant_06;