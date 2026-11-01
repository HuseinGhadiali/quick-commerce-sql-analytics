-- Q22. Are coupons buying growth or just giving away margin? AOV, discount rate and
--      contribution after product cost, by coupon (2025, delivered orders).
-- Skills: COALESCE for NULL dimensions, joining an item-level aggregate back to orders
WITH order_cost AS (
    SELECT order_id, SUM(quantity * unit_cost) AS cogs
    FROM order_items GROUP BY order_id
)
SELECT COALESCE(o.coupon_code, 'No coupon')                                               AS coupon,
       COUNT(*)                                                                            AS orders,
       ROUND((100.0 * COUNT(*) / SUM(COUNT(*)) OVER ())::numeric, 1)                       AS share_of_orders_pct,
       ROUND(AVG(o.item_total)::numeric, 0)                                                AS avg_cart_value,
       ROUND((100.0 * SUM(o.discount_amount) / SUM(o.item_total))::numeric, 1)             AS discount_pct_of_cart,
       ROUND(AVG(o.item_total - oc.cogs - o.discount_amount + o.delivery_fee)::numeric, 1) AS contribution_per_order
FROM orders o
JOIN order_cost oc ON oc.order_id = o.order_id
WHERE o.order_status = 'Delivered' AND o.order_ts >= DATE '2025-01-01'
GROUP BY 1
ORDER BY orders DESC;
