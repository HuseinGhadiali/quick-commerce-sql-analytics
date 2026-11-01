-- Q23. Festive season tracker (Oct-Nov 2025): daily GMV, 7-day moving average and
--      month-to-date running total.
-- Skills: window frames (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), PARTITION BY month for MTD
WITH daily AS (
    SELECT order_ts::date AS order_date, SUM(order_value) AS gmv, COUNT(*) AS orders
    FROM orders
    WHERE order_status = 'Delivered'
      AND order_ts >= DATE '2025-09-24' AND order_ts < DATE '2025-12-01'
    GROUP BY 1
),
calc AS (
    SELECT order_date, orders,
           gmv,
           AVG(gmv) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)            AS gmv_7d_avg,
           SUM(gmv) OVER (PARTITION BY DATE_TRUNC('month', order_date) ORDER BY order_date)        AS gmv_mtd
    FROM daily
)
SELECT order_date, orders,
       ROUND(gmv::numeric / 100000, 2)        AS gmv_lakh,
       ROUND(gmv_7d_avg::numeric / 100000, 2) AS gmv_7d_avg_lakh,
       ROUND(gmv_mtd::numeric / 100000, 1)    AS gmv_mtd_lakh
FROM calc
WHERE order_date >= DATE '2025-10-01'
ORDER BY order_date;
