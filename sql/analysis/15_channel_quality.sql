-- Q15. Which acquisition channel brings the best customers? 90-day repeat rate and
--      180-day revenue per customer (customers who signed up before Jul-2025 so everyone has 180 days).
-- Skills: LEFT JOIN with time-bounded conditions, per-customer aggregation then per-channel aggregation
WITH cust AS (
    SELECT c.customer_id, c.acquisition_channel, c.signup_date,
           COUNT(o.order_id) FILTER (WHERE o.order_ts::date >  c.signup_date
                                       AND o.order_ts::date <= c.signup_date + 90)  AS repeat_orders_90d,
           COALESCE(SUM(o.order_value) FILTER (WHERE o.order_ts::date <= c.signup_date + 180), 0) AS revenue_180d,
           MAX(CASE WHEN o.coupon_code = 'WELCOME50' THEN 1 ELSE 0 END)                AS used_welcome_coupon
    FROM customers c
    LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status = 'Delivered'
    WHERE c.signup_date < DATE '2025-07-01'
    GROUP BY c.customer_id, c.acquisition_channel, c.signup_date
)
SELECT acquisition_channel,
       COUNT(*)                                                                         AS customers,
       ROUND(100 * AVG(CASE WHEN repeat_orders_90d > 0 THEN 1.0 ELSE 0 END)::numeric, 1) AS repeat_90d_pct,
       ROUND(AVG(repeat_orders_90d)::numeric, 2)                                        AS avg_repeat_orders_90d,
       ROUND(AVG(revenue_180d)::numeric, 0)                                             AS revenue_per_customer_180d,
       ROUND(100 * AVG(used_welcome_coupon)::numeric, 1)                                AS welcome_coupon_pct
FROM cust
GROUP BY acquisition_channel
ORDER BY revenue_per_customer_180d DESC;
