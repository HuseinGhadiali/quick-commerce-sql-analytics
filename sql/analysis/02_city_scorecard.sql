-- Q02. City scorecard for 2025: GMV, share of business, rank and YoY growth.
-- Skills: conditional aggregation, window SUM() OVER () for share, RANK()
WITH city_year AS (
    SELECT
        c.city_name,
        c.city_tier,
        SUM(o.order_value) FILTER (WHERE EXTRACT(YEAR FROM o.order_ts) = 2025) AS gmv_2025,
        SUM(o.order_value) FILTER (WHERE EXTRACT(YEAR FROM o.order_ts) = 2024) AS gmv_2024,
        COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM o.order_ts) = 2025)           AS orders_2025,
        COUNT(DISTINCT o.store_id)                                             AS stores
    FROM orders o
    JOIN dark_stores s ON s.store_id = o.store_id
    JOIN cities c      ON c.city_id = s.city_id
    WHERE o.order_status = 'Delivered'
    GROUP BY c.city_name, c.city_tier
)
SELECT
    RANK() OVER (ORDER BY gmv_2025 DESC)                                   AS gmv_rank,
    city_name,
    city_tier,
    stores,
    ROUND(gmv_2025::numeric / 10000000, 2)                                 AS gmv_2025_crore,
    ROUND((100.0 * gmv_2025 / SUM(gmv_2025) OVER ())::numeric, 1)          AS gmv_share_pct,
    ROUND((100.0 * (gmv_2025 - gmv_2024) / gmv_2024)::numeric, 1)          AS yoy_growth_pct,
    ROUND((orders_2025 / 365.0 / stores)::numeric, 1)                      AS orders_per_store_per_day
FROM city_year
ORDER BY gmv_rank;
