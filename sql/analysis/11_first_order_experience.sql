-- Q11. Does a late FIRST delivery cost us the customer?
--      Compare 60-day repeat rate and 90-day order count by first-order lateness.
-- Skills: ROW_NUMBER() to isolate first order, interval filters, cohort comparison
WITH ranked AS (
    SELECT o.customer_id, o.order_id, o.order_ts, o.order_status,
           ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_ts) AS rn
    FROM orders o
),
first_orders AS (
    SELECT r.customer_id, r.order_ts AS first_ts,
           CASE WHEN r.order_status = 'Cancelled'                          THEN 'Cancelled'
                WHEN d.actual_minutes <= d.promised_minutes                 THEN '1. On time'
                WHEN d.actual_minutes <= d.promised_minutes + 4             THEN '2. Late by <= 4 min'
                ELSE '3. Late by > 4 min' END                              AS first_experience
    FROM ranked r
    LEFT JOIN deliveries d ON d.order_id = r.order_id
    WHERE r.rn = 1
      AND r.order_ts < TIMESTAMP '2025-10-01'          -- leave a full 90-day observation window
),
follow_up AS (
    SELECT f.customer_id, f.first_experience,
           COUNT(o.order_id) FILTER (WHERE o.order_ts >  f.first_ts AND o.order_ts <= f.first_ts + INTERVAL '60 days') AS orders_60d,
           COUNT(o.order_id) FILTER (WHERE o.order_ts >  f.first_ts AND o.order_ts <= f.first_ts + INTERVAL '90 days') AS orders_90d
    FROM first_orders f
    LEFT JOIN orders o ON o.customer_id = f.customer_id
    GROUP BY f.customer_id, f.first_experience
)
SELECT first_experience,
       COUNT(*)                                                                 AS customers,
       ROUND(100 * AVG(CASE WHEN orders_60d > 0 THEN 1.0 ELSE 0 END)::numeric, 1) AS repeat_within_60d_pct,
       ROUND(AVG(orders_90d)::numeric, 2)                                       AS avg_orders_next_90d
FROM follow_up
GROUP BY first_experience
ORDER BY first_experience;
