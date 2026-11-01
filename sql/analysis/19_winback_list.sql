-- Q19. Win-back target list: top-quartile lifetime spenders who have not ordered in 45+ days.
--      Summary by city (the full list is a simple SELECT on the same CTE).
-- Skills: NTILE for quartiles, HAVING-style filtering on aggregates, actionable output
WITH lifetime AS (
    SELECT o.customer_id, cu.city_id,
           SUM(o.order_value)                         AS lifetime_spend,
           COUNT(*)                                   AS lifetime_orders,
           DATE '2025-12-31' - MAX(o.order_ts)::date  AS days_since_last_order
    FROM orders o
    JOIN customers cu ON cu.customer_id = o.customer_id
    WHERE o.order_status = 'Delivered'
    GROUP BY o.customer_id, cu.city_id
),
quartiled AS (
    SELECT *, NTILE(4) OVER (ORDER BY lifetime_spend, customer_id) AS spend_quartile FROM lifetime
)
SELECT c.city_name,
       COUNT(*)                                          AS lapsed_high_value_customers,
       ROUND(SUM(q.lifetime_spend)::numeric / 100000, 1) AS their_lifetime_spend_lakh,
       ROUND(AVG(q.lifetime_orders)::numeric, 1)         AS avg_lifetime_orders,
       ROUND(AVG(q.days_since_last_order)::numeric, 0)   AS avg_days_lapsed
FROM quartiled q
JOIN cities c ON c.city_id = q.city_id
WHERE q.spend_quartile = 4 AND q.days_since_last_order > 45
GROUP BY c.city_name
ORDER BY lapsed_high_value_customers DESC;
