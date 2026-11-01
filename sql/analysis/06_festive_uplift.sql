-- Q06. How big is the festive spike? Orders/day and AOV in the festive window vs the
--      28 days before it, and which categories over-index.
-- Skills: VALUES-list CTE, range join, baseline comparison
WITH festivals(festival, fest_date, lead_days) AS (
    VALUES ('Holi 2025', DATE '2025-03-14', 2),
           ('Raksha Bandhan 2025', DATE '2025-08-09', 1),
           ('Ganesh Chaturthi 2025', DATE '2025-08-27', 2),
           ('Diwali 2025', DATE '2025-10-20', 5),
           ('New Year''s Eve 2025', DATE '2025-12-31', 0)
),
daily AS (
    SELECT order_ts::date AS d, COUNT(*) AS orders, SUM(order_value) AS gmv
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY 1
),
windows AS (
    SELECT f.festival,
           AVG(dl.orders) FILTER (WHERE dl.d BETWEEN f.fest_date - f.lead_days AND f.fest_date)  AS fest_orders_per_day,
           AVG(dl.orders) FILTER (WHERE dl.d BETWEEN f.fest_date - 35 AND f.fest_date - 8)        AS base_orders_per_day,
           SUM(dl.gmv) FILTER (WHERE dl.d BETWEEN f.fest_date - f.lead_days AND f.fest_date)
             / SUM(dl.orders) FILTER (WHERE dl.d BETWEEN f.fest_date - f.lead_days AND f.fest_date) AS fest_aov,
           SUM(dl.gmv) FILTER (WHERE dl.d BETWEEN f.fest_date - 35 AND f.fest_date - 8)
             / SUM(dl.orders) FILTER (WHERE dl.d BETWEEN f.fest_date - 35 AND f.fest_date - 8)     AS base_aov
    FROM festivals f
    JOIN daily dl ON dl.d BETWEEN f.fest_date - 35 AND f.fest_date
    GROUP BY f.festival
)
SELECT festival,
       ROUND(fest_orders_per_day::numeric, 0)                                         AS festive_orders_per_day,
       ROUND(base_orders_per_day::numeric, 0)                                         AS baseline_orders_per_day,
       ROUND((100.0 * (fest_orders_per_day / base_orders_per_day - 1))::numeric, 1)   AS order_uplift_pct,
       ROUND(fest_aov::numeric, 0)                                                    AS festive_aov,
       ROUND(base_aov::numeric, 0)                                                    AS baseline_aov
FROM windows
ORDER BY order_uplift_pct DESC;
