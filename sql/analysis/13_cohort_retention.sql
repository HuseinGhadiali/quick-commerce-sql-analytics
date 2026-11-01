-- Q13. Monthly acquisition cohorts: what share of each cohort is still ordering 1, 2, 3, 6, 12 months later?
--      Months not yet observable for a cohort (after Dec-2025) are NULL, not 0.
-- Skills: cohort analysis, MIN() OVER (PARTITION BY), month-difference arithmetic, pivot
WITH activity AS (
    SELECT customer_id,
           DATE_TRUNC('month', order_ts)::date                                AS active_month,
           MIN(DATE_TRUNC('month', order_ts)::date) OVER (PARTITION BY customer_id) AS cohort_month
    FROM orders
    WHERE order_status = 'Delivered'
),
cohort_activity AS (
    SELECT DISTINCT customer_id, cohort_month,
           (EXTRACT(YEAR FROM active_month) - EXTRACT(YEAR FROM cohort_month)) * 12
             + EXTRACT(MONTH FROM active_month) - EXTRACT(MONTH FROM cohort_month) AS month_n
    FROM activity
),
sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohort_activity WHERE month_n = 0 GROUP BY cohort_month
)
SELECT ca.cohort_month,
       s.cohort_size,
       CASE WHEN ca.cohort_month + INTERVAL '1 months' <= DATE '2025-12-01' THEN
       ROUND((100.0 * COUNT(DISTINCT ca.customer_id) FILTER (WHERE month_n = 1)  / s.cohort_size)::numeric, 1) END AS m1_pct,
       CASE WHEN ca.cohort_month + INTERVAL '2 months' <= DATE '2025-12-01' THEN
       ROUND((100.0 * COUNT(DISTINCT ca.customer_id) FILTER (WHERE month_n = 2)  / s.cohort_size)::numeric, 1) END AS m2_pct,
       CASE WHEN ca.cohort_month + INTERVAL '3 months' <= DATE '2025-12-01' THEN
       ROUND((100.0 * COUNT(DISTINCT ca.customer_id) FILTER (WHERE month_n = 3)  / s.cohort_size)::numeric, 1) END AS m3_pct,
       CASE WHEN ca.cohort_month + INTERVAL '6 months' <= DATE '2025-12-01' THEN
       ROUND((100.0 * COUNT(DISTINCT ca.customer_id) FILTER (WHERE month_n = 6)  / s.cohort_size)::numeric, 1) END AS m6_pct,
       CASE WHEN ca.cohort_month + INTERVAL '12 months' <= DATE '2025-12-01' THEN
       ROUND((100.0 * COUNT(DISTINCT ca.customer_id) FILTER (WHERE month_n = 12) / s.cohort_size)::numeric, 1) END AS m12_pct
FROM cohort_activity ca
JOIN sizes s ON s.cohort_month = ca.cohort_month
GROUP BY ca.cohort_month, s.cohort_size
ORDER BY ca.cohort_month;
