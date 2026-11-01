-- Q04. Pareto check: how many SKUs drive 80% of revenue?
-- Skills: running total with SUM() OVER (ORDER BY ... ROWS UNBOUNDED PRECEDING)
WITH sku_rev AS (
    SELECT p.product_id, p.product_name, p.category,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi
    JOIN orders o   ON o.order_id = oi.order_id AND o.order_status = 'Delivered'
    JOIN products p ON p.product_id = oi.product_id
    GROUP BY p.product_id, p.product_name, p.category
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY revenue DESC)                                        AS sku_rank,
           COUNT(*) OVER ()                                                                 AS total_skus,
           SUM(revenue) OVER (ORDER BY revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(revenue) OVER ()                                                         AS cum_share
    FROM sku_rev
)
SELECT sku_rank, product_name, category,
       ROUND(revenue::numeric / 100000, 1)                     AS revenue_lakh,
       ROUND((100.0 * cum_share)::numeric, 1)                  AS cumulative_revenue_pct,
       ROUND((100.0 * sku_rank / total_skus)::numeric, 1)      AS cumulative_sku_pct
FROM ranked
WHERE cum_share <= 0.80 OR sku_rank <= 10
ORDER BY sku_rank;
