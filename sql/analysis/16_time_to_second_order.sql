-- Q16. How long until a new customer orders again? Distribution of days between 1st and 2nd order.
-- Skills: LEAD(), ROW_NUMBER(), bucketing, PERCENTILE_CONT
WITH seq AS (
    SELECT customer_id, order_ts,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_ts)   AS rn,
           LEAD(order_ts) OVER (PARTITION BY customer_id ORDER BY order_ts) AS next_ts
    FROM orders
    WHERE order_status = 'Delivered'
),
gaps AS (
    SELECT customer_id, next_ts::date - order_ts::date AS gap_days
    FROM seq
    WHERE rn = 1 AND next_ts IS NOT NULL
),
buckets AS (
    SELECT CASE WHEN gap_days <= 3  THEN '1. 0-3 days'
                WHEN gap_days <= 7  THEN '2. 4-7 days'
                WHEN gap_days <= 14 THEN '3. 8-14 days'
                WHEN gap_days <= 30 THEN '4. 15-30 days'
                WHEN gap_days <= 60 THEN '5. 31-60 days'
                ELSE '6. 60+ days' END AS gap_bucket, gap_days
    FROM gaps
)
SELECT gap_bucket,
       COUNT(*)                                                                  AS customers,
       ROUND((100.0 * COUNT(*) / SUM(COUNT(*)) OVER ())::numeric, 1)             AS pct,
       ROUND((100.0 * SUM(COUNT(*)) OVER (ORDER BY gap_bucket) / SUM(COUNT(*)) OVER ())::numeric, 1) AS cumulative_pct,
       (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY gap_days) FROM gaps)  AS overall_median_days
FROM buckets
GROUP BY gap_bucket
ORDER BY gap_bucket;
