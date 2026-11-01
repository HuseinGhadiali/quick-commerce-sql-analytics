-- Q09. How much does the Mumbai monsoon hurt operations? Mumbai vs other cities,
--      monsoon (Jun-Sep) vs rest of year, 2024-2025.
-- Skills: CASE-derived dimensions, LEFT JOIN to keep cancelled orders, difference-in-differences style read
WITH base AS (
    SELECT CASE WHEN c.city_name = 'Mumbai' THEN 'Mumbai' ELSE 'Other cities' END            AS city_group,
           CASE WHEN EXTRACT(MONTH FROM o.order_ts) BETWEEN 6 AND 9 THEN 'Monsoon (Jun-Sep)'
                ELSE 'Rest of year' END                                                       AS season,
           o.order_status, o.cancel_reason, d.actual_minutes, d.promised_minutes
    FROM orders o
    JOIN dark_stores s    ON s.store_id = o.store_id
    JOIN cities c         ON c.city_id = s.city_id
    LEFT JOIN deliveries d ON d.order_id = o.order_id
)
SELECT city_group, season,
       COUNT(*)                                                                                      AS orders,
       ROUND(AVG(actual_minutes)::numeric, 1)                                                        AS avg_delivery_min,
       ROUND(100 * AVG(CASE WHEN actual_minutes <= promised_minutes THEN 1.0
                            WHEN actual_minutes IS NOT NULL THEN 0 END)::numeric, 1)                 AS on_time_pct,
       ROUND((100.0 * COUNT(*) FILTER (WHERE cancel_reason = 'Rider unavailable') / COUNT(*))::numeric, 2) AS rider_cancel_pct
FROM base
GROUP BY city_group, season
ORDER BY city_group, season;
