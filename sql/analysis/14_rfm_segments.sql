-- Q14. RFM segmentation as of 31-Dec-2025 with NTILE scores and named segments.
-- Skills: NTILE(5), CASE-based segment rules, revenue concentration
WITH rfm_raw AS (
    SELECT customer_id,
           DATE '2025-12-31' - MAX(order_ts)::date   AS recency_days,
           COUNT(*)                                   AS frequency,
           SUM(order_value)                           AS monetary
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY customer_id
),
scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC, customer_id) AS r,   -- 5 = most recent; id breaks ties deterministically
           NTILE(5) OVER (ORDER BY frequency, customer_id)              AS f,
           NTILE(5) OVER (ORDER BY monetary, customer_id)               AS m
    FROM rfm_raw
),
segmented AS (
    SELECT *,
           CASE WHEN r >= 4 AND f >= 4                 THEN '1. Champions'
                WHEN r >= 3 AND f >= 3                 THEN '2. Loyal'
                WHEN r >= 4 AND f <= 2                 THEN '3. New / Promising'
                WHEN r = 3  AND f <= 2                 THEN '4. Need attention'
                WHEN r <= 2 AND f >= 3                 THEN '5. At risk (were valuable)'
                ELSE                                        '6. Hibernating / lost' END AS segment
    FROM scored
)
SELECT segment,
       COUNT(*)                                                                    AS customers,
       ROUND((100.0 * COUNT(*) / SUM(COUNT(*)) OVER ())::numeric, 1)               AS customer_pct,
       ROUND((100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER ())::numeric, 1)     AS revenue_pct,
       ROUND(AVG(recency_days)::numeric, 0)                                        AS avg_recency_days,
       ROUND(AVG(frequency)::numeric, 1)                                           AS avg_orders,
       ROUND(AVG(monetary)::numeric, 0)                                            AS avg_lifetime_spend
FROM segmented
GROUP BY segment
ORDER BY segment;
