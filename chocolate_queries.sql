USE Chocolate_DB;

-- Country query
		-- Boxes shipped (Discarded the returns) - 1
SELECT
    country,
    COUNT(order_id) AS total_orders,
    SUM(boxes_shipped) AS total_boxes,
    SUM(amount_after_discount) AS total_revenue,
    SUM(marketing_spend) AS total_marketing_spend,
    SUM(amount_after_discount) / SUM(marketing_spend) AS marketing_roi,
    AVG(amount_after_discount) AS avg_order_value
FROM invoices
WHERE amount_after_discount >= 0 AND boxes_shipped >= 0 -- this is to discard the returns
GROUP BY country
ORDER BY total_revenue DESC;

		-- Boxes returned - 2
SELECT
    country,
    COUNT(order_id) AS total_orders,
    SUM(boxes_shipped) AS total_boxes,
    SUM(amount_after_discount) AS total_revenue,
    SUM(marketing_spend) AS total_marketing_spend,
    SUM(amount_after_discount) / SUM(marketing_spend) AS marketing_roi,
    AVG(amount_after_discount) AS avg_order_value
FROM invoices
WHERE amount_after_discount < 0 AND boxes_shipped < 0 -- this is to discard the returns
GROUP BY country
ORDER BY total_revenue DESC;

-- product by total boxes sold - 3
SELECT
    p.product,
    SUM(i.boxes_shipped) AS total_boxes,
    SUM(i.amount_after_discount) AS total_revenue,
    AVG(i.discount_pct) AS avg_discount
FROM invoices i
JOIN products p
    ON i.product_id = p.product_id
WHERE amount_after_discount >= 0 AND boxes_shipped >= 0 -- this is to discard the returns
GROUP BY p.product
ORDER BY total_boxes DESC;

-- product by revenue - 4

SELECT
    p.product,
    SUM(i.boxes_shipped) AS total_boxes,
    SUM(i.amount_after_discount) AS total_revenue,
    AVG(i.discount_pct) AS avg_discount
FROM invoices i
JOIN products p
    ON i.product_id = p.product_id
WHERE amount_after_discount >= 0 AND boxes_shipped >= 0 -- this is to discard the returns
GROUP BY p.product
ORDER BY total_revenue DESC;


-- channel performance - 5

SELECT
    channel,
    COUNT(order_id) AS total_orders,
    SUM(boxes_shipped) AS total_boxes,
    SUM(amount_after_discount) AS total_revenue,
    AVG(discount_pct) AS avg_discount,
    AVG(amount_after_discount) AS avg_order_value
FROM invoices
WHERE amount_after_discount >= 0 AND boxes_shipped >= 0 -- this is to discard the returns
GROUP BY channel HAVING total_orders > 0 -- HERE YOU HAVE THE HAVING
ORDER BY total_revenue DESC;

-- Retail will be my own store or supermarket eg -> more extensive in logistics 
-- wholesale is b2b or company that will do transformation
-- adjust prices or discounts to be less competitive in Wholesale - competitors may be much higher in price 


-- MONTHLY - 6

SELECT
    MONTH(order_date) AS sales_month,
    SUM(amount_after_discount) AS monthly_revenue,
    SUM(boxes_shipped) AS monthly_boxes
FROM invoices
WHERE amount_after_discount >= 0 AND boxes_shipped >= 0 -- this is to discard the returns
GROUP BY MONTH(order_date)
ORDER BY sales_month;

-- need visualization to be done in python


-- TOP SALESPEOPLE - 7
SELECT
    s.salesperson,
    COUNT(i.order_id) AS total_orders,
    SUM(i.amount_after_discount) AS total_revenue,
    SUM(i.boxes_shipped) AS total_boxes,
    AVG(i.discount_pct) AS avg_discount,
    AVG(i.amount_after_discount) AS avg_order_value
FROM invoices i
JOIN salespersons s
    ON i.salesperson_id = s.salesperson_id
WHERE amount_after_discount >= 0 AND boxes_shipped >= 0 -- this is to discard the returns
GROUP BY s.salesperson
ORDER BY total_revenue DESC
LIMIT 10;

-- best product by country - 8 (Used to confirm products to be sold in the country we're going to open)

SELECT
    country,
    product,
    total_revenue
FROM (
    SELECT
        i.country,
        p.product,
        SUM(i.amount_after_discount) AS total_revenue,
        RANK() OVER (
            PARTITION BY i.country
            ORDER BY SUM(i.amount_after_discount) DESC
        ) AS product_rank
    FROM invoices i
    JOIN products p
        ON i.product_id = p.product_id
    WHERE i.amount_after_discount >= 0
      AND i.boxes_shipped >= 0
    GROUP BY i.country, p.product
) ranked_products
WHERE product_rank = 1;


-- on total boxes - 9
SELECT
    country,
    product,
    total_boxes
FROM (
    SELECT
        i.country,
        p.product,
        SUM(i.boxes_shipped) AS total_boxes,
        RANK() OVER (
            PARTITION BY i.country
            ORDER BY SUM(i.boxes_shipped) DESC
        ) AS product_rank
    FROM invoices i
    JOIN products p
        ON i.product_id = p.product_id
    WHERE i.amount_after_discount >= 0
      AND i.boxes_shipped >= 0
    GROUP BY i.country, p.product
) ranked_products
WHERE product_rank = 1;

-- DO DISCOUNT INCREASE VOLUME? - 10


SELECT
    CASE
        WHEN discount_pct = 0 THEN 'No discount'
        WHEN discount_pct <= 10 THEN 'Low discount'
        WHEN discount_pct <= 20 THEN 'Medium discount'
        ELSE 'High discount'
    END AS discount_group,
    COUNT(order_id) AS total_orders,
    AVG(boxes_shipped) AS avg_boxes_shipped,
    SUM(amount_after_discount) AS total_revenue
FROM invoices
WHERE amount_after_discount >= 0 AND boxes_shipped >= 0 
GROUP BY discount_group
ORDER BY total_revenue DESC;

-- We'll revise the high discount policy to increase sales





