-- Q10. Why are orders cancelled, and when? Cancellation rate by reason and time band (2025).
-- Skills: CASE bucketing, conditional counts, share of total
WITH o AS (
    SELECT CASE WHEN EXTRACT(HOUR FROM order_ts) BETWEEN 6 AND 10  THEN '1. Morning 6-11'
                WHEN EXTRACT(HOUR FROM order_ts) BETWEEN 11 AND 16 THEN '2. Afternoon 11-17'
                WHEN EXTRACT(HOUR FROM order_ts) BETWEEN 17 AND 22 THEN '3. Evening 17-23'
                ELSE '4. Late night 23-6' END AS time_band,
           order_status, cancel_reason
    FROM orders
    WHERE order_ts >= DATE '2025-01-01'
)
SELECT time_band,
       COUNT(*)                                                                                         AS orders,
       ROUND((100.0 * COUNT(*) FILTER (WHERE order_status = 'Cancelled') / COUNT(*))::numeric, 2)       AS cancel_rate_pct,
       ROUND((100.0 * COUNT(*) FILTER (WHERE cancel_reason = 'Rider unavailable') / COUNT(*))::numeric, 2)  AS rider_unavailable_pct,
       ROUND((100.0 * COUNT(*) FILTER (WHERE cancel_reason = 'Item out of stock') / COUNT(*))::numeric, 2)  AS out_of_stock_pct,
       ROUND((100.0 * COUNT(*) FILTER (WHERE cancel_reason = 'Customer cancelled') / COUNT(*))::numeric, 2) AS customer_cancel_pct
FROM o
GROUP BY time_band
ORDER BY time_band;
