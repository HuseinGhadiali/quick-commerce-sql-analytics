-- Q01. How is the business trending month over month and year over year?
-- Skills: CTE, DATE_TRUNC, LAG window function, growth %
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', order_ts)::date                         AS month,
        COUNT(*) FILTER (WHERE order_status = 'Delivered')          AS delivered_orders,
        SUM(order_value) FILTER (WHERE order_status = 'Delivered')  AS gmv,
        COUNT(DISTINCT customer_id)                                 AS active_customers
    FROM orders
    GROUP BY 1
)
SELECT
    month,
    delivered_orders,
    ROUND(gmv::numeric / 100000, 2)                                   AS gmv_lakh,
    ROUND((gmv / delivered_orders)::numeric, 0)                       AS aov,
    active_customers,
    ROUND((100.0 * (gmv - LAG(gmv, 1) OVER w) / LAG(gmv, 1) OVER w)::numeric, 1)   AS gmv_mom_pct,
    ROUND((100.0 * (gmv - LAG(gmv, 12) OVER w) / LAG(gmv, 12) OVER w)::numeric, 1) AS gmv_yoy_pct
FROM monthly
WINDOW w AS (ORDER BY month)
ORDER BY month;
