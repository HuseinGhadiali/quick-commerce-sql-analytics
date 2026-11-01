-- Q08. Which dark stores are operational outliers? Median / p90 delivery time and on-time %
--      ranked within their city, flagged when > 1.5 min slower than the city median store.
-- Skills: PERCENTILE_CONT ... WITHIN GROUP, RANK() OVER (PARTITION BY), median-of-medians baseline
WITH store_perf AS (
    SELECT s.store_id, s.store_code, c.city_name,
           COUNT(*)                                                                  AS deliveries,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY d.actual_minutes)              AS p50_min,
           PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY d.actual_minutes)              AS p90_min,
           AVG(CASE WHEN d.actual_minutes <= d.promised_minutes THEN 1.0 ELSE 0 END) AS on_time,
           AVG(d.customer_rating)                                                     AS avg_rating
    FROM deliveries d
    JOIN orders o      ON o.order_id = d.order_id
    JOIN dark_stores s ON s.store_id = o.store_id
    JOIN cities c      ON c.city_id = s.city_id
    WHERE o.order_ts >= DATE '2025-01-01'
    GROUP BY s.store_id, s.store_code, c.city_name
),
city_median AS (   -- ordered-set aggregates are not window functions in PostgreSQL, so aggregate separately
    SELECT city_name, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY p50_min) AS city_median_p50
    FROM store_perf
    GROUP BY city_name
),
with_city AS (
    SELECT sp.*, cm.city_median_p50,
           RANK() OVER (PARTITION BY sp.city_name ORDER BY sp.p50_min DESC) AS slowest_rank_in_city
    FROM store_perf sp
    JOIN city_median cm ON cm.city_name = sp.city_name
)
SELECT store_code, city_name, deliveries,
       ROUND(p50_min::numeric, 1)                         AS p50_minutes,
       ROUND(p90_min::numeric, 1)                         AS p90_minutes,
       ROUND(100 * on_time::numeric, 1)                   AS on_time_pct,
       ROUND(avg_rating::numeric, 2)                      AS avg_rating,
       slowest_rank_in_city,
       ROUND((p50_min - city_median_p50)::numeric, 1)     AS minutes_vs_city_median,
       CASE WHEN p50_min - city_median_p50 > 1.5 THEN 'INVESTIGATE' ELSE 'ok' END AS flag
FROM with_city
ORDER BY minutes_vs_city_median DESC, store_code
LIMIT 12;
