-- Data-quality checks. Every query returns the number of VIOLATING rows; all should be 0.
-- These run in CI (tests/test_data_quality.py) before any analysis is trusted.

-- name: orders_without_items
SELECT COUNT(*) FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = o.order_id);

-- name: item_total_does_not_reconcile
SELECT COUNT(*) FROM orders o
JOIN (SELECT order_id, SUM(quantity * unit_price) AS calc FROM order_items GROUP BY order_id) x
  ON x.order_id = o.order_id
WHERE ABS(o.item_total - x.calc) > 0.01;

-- name: order_value_does_not_reconcile
SELECT COUNT(*) FROM orders
WHERE ABS(order_value - (item_total - discount_amount + delivery_fee)) > 0.01;

-- name: delivered_orders_missing_delivery_row
SELECT COUNT(*) FROM orders o
WHERE o.order_status = 'Delivered'
  AND NOT EXISTS (SELECT 1 FROM deliveries d WHERE d.order_id = o.order_id);

-- name: cancelled_orders_with_delivery_row
SELECT COUNT(*) FROM deliveries d JOIN orders o ON o.order_id = d.order_id
WHERE o.order_status = 'Cancelled';

-- name: cancelled_without_reason
SELECT COUNT(*) FROM orders WHERE order_status = 'Cancelled' AND cancel_reason IS NULL;

-- name: order_before_customer_signup
SELECT COUNT(*) FROM orders o JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_ts::date < c.signup_date;

-- name: order_before_store_launch
SELECT COUNT(*) FROM orders o JOIN dark_stores s ON s.store_id = o.store_id
WHERE o.order_ts::date < s.launch_date;

-- name: customer_ordering_from_other_city
SELECT COUNT(*) FROM orders o
JOIN customers c   ON c.customer_id = o.customer_id
JOIN dark_stores s ON s.store_id = o.store_id
WHERE c.city_id <> s.city_id;

-- name: selling_price_above_mrp
SELECT COUNT(*) FROM products WHERE selling_price > mrp;

-- name: negative_or_zero_amounts
SELECT COUNT(*) FROM order_items WHERE quantity <= 0 OR unit_price <= 0 OR unit_cost < 0;

-- name: delivered_before_ordered
SELECT COUNT(*) FROM deliveries d JOIN orders o ON o.order_id = d.order_id
WHERE d.delivered_ts < o.order_ts;

-- name: rating_out_of_range
SELECT COUNT(*) FROM deliveries WHERE customer_rating IS NOT NULL AND customer_rating NOT BETWEEN 1 AND 5;
