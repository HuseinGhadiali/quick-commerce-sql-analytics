-- Q12. How fast do new dark stores ramp up? Orders/day and delivery time by week since launch
--      for stores launched in the data window.
-- Skills: date arithmetic, integer bucketing, AVG over a derived dimension
WITH new_stores AS (
    SELECT store_id, store_code, launch_date
    FROM dark_stores
    WHERE launch_date BETWEEN DATE '2024-01-01' AND DATE '2025-09-30'
),
weekly AS (
    SELECT ns.store_code,
           FLOOR((o.order_ts::date - ns.launch_date) / 7) + 1     AS week_since_launch,
           COUNT(*) / 7.0                                         AS orders_per_day,
           AVG(d.actual_minutes)                                  AS avg_minutes
    FROM new_stores ns
    JOIN orders o          ON o.store_id = ns.store_id
    LEFT JOIN deliveries d ON d.order_id = o.order_id
    WHERE o.order_ts::date - ns.launch_date < 12 * 7
    GROUP BY 1, 2
)
SELECT week_since_launch::int                     AS week_since_launch,
       COUNT(*)                                   AS stores,
       ROUND(AVG(orders_per_day)::numeric, 1)     AS avg_orders_per_day,
       ROUND(AVG(avg_minutes)::numeric, 1)        AS avg_delivery_min
FROM weekly
GROUP BY 1
ORDER BY 1;
