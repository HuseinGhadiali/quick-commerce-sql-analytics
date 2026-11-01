-- Q07. On-time delivery % (delivered within the promised minutes) by city and month, 2025.
-- Skills: CASE inside AVG, pivot by month, AVG() OVER (PARTITION BY) for the city average
WITH city_month AS (
    SELECT c.city_name,
           EXTRACT(MONTH FROM o.order_ts)::int AS m,
           AVG(CASE WHEN d.actual_minutes <= d.promised_minutes THEN 1.0 ELSE 0 END) AS on_time
    FROM deliveries d
    JOIN orders o      ON o.order_id = d.order_id
    JOIN dark_stores s ON s.store_id = o.store_id
    JOIN cities c      ON c.city_id = s.city_id
    WHERE o.order_ts >= DATE '2025-01-01'
    GROUP BY 1, 2
)
SELECT city_name,
       ROUND(100 * AVG(on_time)::numeric, 1)                                    AS year_on_time_pct,
       ROUND(100 * MIN(on_time)::numeric, 1)                                    AS worst_month_pct,
       ROUND(100 * MAX(on_time) FILTER (WHERE m = 1)::numeric, 1)               AS jan,
       ROUND(100 * MAX(on_time) FILTER (WHERE m = 4)::numeric, 1)               AS apr,
       ROUND(100 * MAX(on_time) FILTER (WHERE m = 6)::numeric, 1)               AS jun,
       ROUND(100 * MAX(on_time) FILTER (WHERE m = 7)::numeric, 1)               AS jul,
       ROUND(100 * MAX(on_time) FILTER (WHERE m = 8)::numeric, 1)               AS aug,
       ROUND(100 * MAX(on_time) FILTER (WHERE m = 9)::numeric, 1)               AS sep,
       ROUND(100 * MAX(on_time) FILTER (WHERE m = 10)::numeric, 1)              AS oct,
       ROUND(100 * MAX(on_time) FILTER (WHERE m = 12)::numeric, 1)              AS dec
FROM city_month
GROUP BY city_name
ORDER BY year_on_time_pct;
