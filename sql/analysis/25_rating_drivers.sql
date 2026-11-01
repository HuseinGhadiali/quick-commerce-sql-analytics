-- Q25. What drives customer ratings? Average rating and share of 1-2 star ratings by lateness.
-- Skills: CASE bucketing on a derived measure, conditional share
SELECT CASE WHEN actual_minutes <= promised_minutes - 3  THEN '1. Early by 3+ min'
            WHEN actual_minutes <= promised_minutes      THEN '2. On time'
            WHEN actual_minutes <= promised_minutes + 5  THEN '3. Late by 0-5 min'
            WHEN actual_minutes <= promised_minutes + 10 THEN '4. Late by 5-10 min'
            ELSE                                              '5. Late by 10+ min' END   AS delivery_outcome,
       COUNT(*)                                                                         AS rated_orders,
       ROUND(AVG(customer_rating)::numeric, 2)                                          AS avg_rating,
       ROUND((100.0 * COUNT(*) FILTER (WHERE customer_rating <= 2) / COUNT(*))::numeric, 1) AS one_two_star_pct
FROM deliveries
WHERE customer_rating IS NOT NULL
GROUP BY 1
ORDER BY 1;
