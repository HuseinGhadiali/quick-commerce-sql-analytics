-- Q03. Which categories make money? Revenue, gross margin and basket penetration (2025).
-- Skills: multi-table joins, COUNT(DISTINCT), ratio-of-sums (not average-of-ratios)
WITH delivered_items AS (
    SELECT oi.order_id, p.category, p.is_private_label,
           oi.quantity * oi.unit_price AS revenue,
           oi.quantity * oi.unit_cost  AS cogs
    FROM order_items oi
    JOIN orders o   ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.order_status = 'Delivered'
      AND o.order_ts >= DATE '2025-01-01'
),
total AS (SELECT COUNT(DISTINCT order_id) AS n_orders FROM delivered_items)
SELECT
    category,
    ROUND(SUM(revenue)::numeric / 100000, 1)                                       AS revenue_lakh,
    ROUND((100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER ())::numeric, 1)          AS revenue_share_pct,
    ROUND((100.0 * (SUM(revenue) - SUM(cogs)) / SUM(revenue))::numeric, 1)         AS gross_margin_pct,
    ROUND((100.0 * COUNT(DISTINCT order_id) / MAX(t.n_orders))::numeric, 1)        AS order_penetration_pct,
    ROUND((100.0 * SUM(revenue) FILTER (WHERE is_private_label = 1) / SUM(revenue))::numeric, 1) AS private_label_share_pct
FROM delivered_items
CROSS JOIN total t
GROUP BY category
ORDER BY revenue_lakh DESC;
