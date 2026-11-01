-- Q05. When do customers order? Orders by hour of day x day of week (2025).
-- Skills: EXTRACT, pivot with COUNT(*) FILTER (WHERE ...)
SELECT
    EXTRACT(HOUR FROM order_ts)::int                              AS hour_of_day,
    COUNT(*) FILTER (WHERE EXTRACT(DOW FROM order_ts) = 1)        AS mon,
    COUNT(*) FILTER (WHERE EXTRACT(DOW FROM order_ts) = 2)        AS tue,
    COUNT(*) FILTER (WHERE EXTRACT(DOW FROM order_ts) = 3)        AS wed,
    COUNT(*) FILTER (WHERE EXTRACT(DOW FROM order_ts) = 4)        AS thu,
    COUNT(*) FILTER (WHERE EXTRACT(DOW FROM order_ts) = 5)        AS fri,
    COUNT(*) FILTER (WHERE EXTRACT(DOW FROM order_ts) = 6)        AS sat,
    COUNT(*) FILTER (WHERE EXTRACT(DOW FROM order_ts) = 0)        AS sun,
    ROUND((100.0 * COUNT(*) / SUM(COUNT(*)) OVER ())::numeric, 1) AS share_of_day_pct
FROM orders
WHERE order_ts >= DATE '2025-01-01'
GROUP BY 1
ORDER BY 1;
