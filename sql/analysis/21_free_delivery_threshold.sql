-- Q21. Is the Rs 199 free-delivery threshold changing behaviour? Cart-value histogram around it.
-- Skills: FLOOR bucketing, window share, spotting "bunching" just above a threshold
WITH carts AS (
    -- buckets are anchored on the threshold so that [189, 199) and [199, 209) sit either side of it
    SELECT 199 + FLOOR((item_total - 199) / 10) * 10 AS bucket_start
    FROM orders
    WHERE order_ts >= DATE '2025-01-01' AND item_total >= 119 AND item_total < 279
)
SELECT bucket_start::int                                   AS cart_value_from,
       (bucket_start + 9)::int                             AS cart_value_to,
       COUNT(*)                                            AS orders,
       CASE WHEN bucket_start = 189 THEN 'just below threshold (pays delivery fee)'
            WHEN bucket_start = 199 THEN 'just above threshold (free delivery)'
            ELSE '' END                                     AS note
FROM carts
GROUP BY bucket_start
ORDER BY bucket_start;
