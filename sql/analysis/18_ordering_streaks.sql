-- Q18. Habit formation: longest run of consecutive weeks with at least one order (gaps & islands).
-- Skills: gaps-and-islands with (week_index - ROW_NUMBER()), streak length distribution
WITH weeks AS (
    SELECT DISTINCT customer_id,
           FLOOR((order_ts::date - DATE '2024-01-01') / 7.0) AS week_idx   -- explicit FLOOR: '/' is float division in DuckDB
    FROM orders
    WHERE order_status = 'Delivered'
),
islands AS (
    SELECT customer_id, week_idx,
           week_idx - ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY week_idx) AS island_id
    FROM weeks
),
streaks AS (
    SELECT customer_id, island_id, COUNT(*) AS streak_weeks
    FROM islands
    GROUP BY customer_id, island_id
),
best AS (
    SELECT customer_id, MAX(streak_weeks) AS longest_streak FROM streaks GROUP BY customer_id
)
SELECT CASE WHEN longest_streak = 1  THEN '1 week'
            WHEN longest_streak <= 3 THEN '2-3 weeks'
            WHEN longest_streak <= 7 THEN '4-7 weeks'
            WHEN longest_streak <= 15 THEN '8-15 weeks'
            ELSE '16+ weeks' END                                       AS longest_weekly_streak,
       COUNT(*)                                                        AS customers,
       ROUND((100.0 * COUNT(*) / SUM(COUNT(*)) OVER ())::numeric, 1)   AS pct,
       MAX(longest_streak)                                             AS max_in_bucket
FROM best
GROUP BY 1
ORDER BY MIN(longest_streak);
