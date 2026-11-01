-- Q24. Unit economics per order by city (2025). Contribution = item revenue - product cost
--      - discount + delivery fee - delivery cost. Delivery cost is an ASSUMPTION:
--      Rs 22 fixed per drop + Rs 6 per km (rider payout model), stated here so it can be changed.
-- Skills: business-logic CTEs, assumption parameters as a one-row CTE
WITH params AS (SELECT 22.0 AS fixed_cost_per_drop, 6.0 AS cost_per_km),
order_cost AS (
    SELECT order_id, SUM(quantity * unit_cost) AS cogs FROM order_items GROUP BY order_id
),
econ AS (
    SELECT c.city_name,
           o.item_total, oc.cogs, o.discount_amount, o.delivery_fee,
           p.fixed_cost_per_drop + p.cost_per_km * d.distance_km AS delivery_cost
    FROM orders o
    JOIN deliveries d   ON d.order_id = o.order_id
    JOIN order_cost oc  ON oc.order_id = o.order_id
    JOIN dark_stores s  ON s.store_id = o.store_id
    JOIN cities c       ON c.city_id = s.city_id
    CROSS JOIN params p
    WHERE o.order_ts >= DATE '2025-01-01'
)
SELECT city_name,
       COUNT(*)                                                       AS delivered_orders,
       ROUND(AVG(item_total)::numeric, 0)                             AS aov,
       ROUND(AVG(item_total - cogs)::numeric, 1)                      AS gross_margin_per_order,
       ROUND(AVG(discount_amount)::numeric, 1)                        AS discount_per_order,
       ROUND(AVG(delivery_fee)::numeric, 1)                           AS delivery_fee_per_order,
       ROUND(AVG(delivery_cost)::numeric, 1)                          AS delivery_cost_per_order,
       ROUND(AVG(item_total - cogs - discount_amount + delivery_fee - delivery_cost)::numeric, 1) AS contribution_per_order,
       ROUND((100.0 * AVG(item_total - cogs - discount_amount + delivery_fee - delivery_cost) / AVG(item_total))::numeric, 1) AS contribution_margin_pct
FROM econ
GROUP BY city_name
ORDER BY contribution_per_order DESC;
