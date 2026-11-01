-- Q17. Top 3 customers by 2025 spend in every city (for a VIP programme pilot).
-- Skills: ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...) "top-N per group"
WITH spend AS (
    SELECT c.city_name, o.customer_id,
           COUNT(*)            AS orders_2025,
           SUM(o.order_value)  AS spend_2025
    FROM orders o
    JOIN customers cu ON cu.customer_id = o.customer_id
    JOIN cities c     ON c.city_id = cu.city_id
    WHERE o.order_status = 'Delivered' AND o.order_ts >= DATE '2025-01-01'
    GROUP BY c.city_name, o.customer_id
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY city_name ORDER BY spend_2025 DESC, customer_id) AS rn
    FROM spend
)
SELECT city_name, rn AS city_rank, customer_id, orders_2025,
       ROUND(spend_2025::numeric, 0) AS spend_2025
FROM ranked
WHERE rn <= 3
ORDER BY city_name, rn;
