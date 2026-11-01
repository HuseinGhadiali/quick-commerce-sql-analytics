-- Q20. Frequently bought together: product pairs with support, confidence and lift (2025).
-- Skills: self-join on order_id with a.product_id < b.product_id, association-rule metrics
WITH baskets AS (
    SELECT oi.order_id, oi.product_id
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.order_status = 'Delivered' AND o.order_ts >= DATE '2025-01-01'
),
n AS (SELECT COUNT(DISTINCT order_id) AS n_orders FROM baskets),
item_freq AS (
    SELECT product_id, COUNT(*) AS orders_with_item FROM baskets GROUP BY product_id
),
pairs AS (
    SELECT a.product_id AS item_a, b.product_id AS item_b, COUNT(*) AS orders_with_pair
    FROM baskets a
    JOIN baskets b ON a.order_id = b.order_id AND a.product_id < b.product_id
    GROUP BY a.product_id, b.product_id
)
SELECT pa.product_name                                                                  AS product_a,
       pb.product_name                                                                  AS product_b,
       p.orders_with_pair,
       ROUND((100.0 * p.orders_with_pair / n.n_orders)::numeric, 2)                     AS support_pct,
       ROUND((100.0 * p.orders_with_pair / fa.orders_with_item)::numeric, 1)            AS confidence_a_to_b_pct,
       ROUND((p.orders_with_pair * 1.0 * n.n_orders
              / (fa.orders_with_item * fb.orders_with_item))::numeric, 2)               AS lift
FROM pairs p
CROSS JOIN n
JOIN item_freq fa ON fa.product_id = p.item_a
JOIN item_freq fb ON fb.product_id = p.item_b
JOIN products pa  ON pa.product_id = p.item_a
JOIN products pb  ON pb.product_id = p.item_b
WHERE p.orders_with_pair >= 300
ORDER BY lift DESC
LIMIT 15;
