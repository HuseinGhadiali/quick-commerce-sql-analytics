-- =====================================================================
-- Quick-commerce analytics: star-ish schema (PostgreSQL / DuckDB compatible)
-- Grain:
--   orders       one row per customer order (incl. cancelled)
--   order_items  one row per product within an order
--   deliveries   one row per delivered order (1:0..1 with orders)
-- =====================================================================
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS deliveries;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS dark_stores;
DROP TABLE IF EXISTS cities;

CREATE TABLE cities (
    city_id     INTEGER PRIMARY KEY,
    city_name   VARCHAR(40) NOT NULL,
    state       VARCHAR(40) NOT NULL,
    city_tier   VARCHAR(10) NOT NULL
);

CREATE TABLE dark_stores (
    store_id    INTEGER PRIMARY KEY,
    city_id     INTEGER NOT NULL REFERENCES cities (city_id),
    store_code  VARCHAR(30) NOT NULL,
    locality    VARCHAR(60) NOT NULL,
    launch_date DATE NOT NULL,
    area_sqft   INTEGER
);

CREATE TABLE customers (
    customer_id         INTEGER PRIMARY KEY,
    city_id             INTEGER NOT NULL REFERENCES cities (city_id),
    signup_date         DATE NOT NULL,
    acquisition_channel VARCHAR(20) NOT NULL,
    age_band            VARCHAR(10)
);

CREATE TABLE products (
    product_id        INTEGER PRIMARY KEY,
    product_name      VARCHAR(80) NOT NULL,
    category          VARCHAR(40) NOT NULL,
    mrp               NUMERIC(10, 2) NOT NULL,
    selling_price     NUMERIC(10, 2) NOT NULL,
    unit_cost         NUMERIC(10, 2) NOT NULL,
    is_private_label  SMALLINT NOT NULL
);

CREATE TABLE orders (
    order_id         BIGINT PRIMARY KEY,
    customer_id      INTEGER NOT NULL REFERENCES customers (customer_id),
    store_id         INTEGER NOT NULL REFERENCES dark_stores (store_id),
    order_ts         TIMESTAMP NOT NULL,
    order_status     VARCHAR(12) NOT NULL,      -- Delivered | Cancelled
    cancel_reason    VARCHAR(30),
    payment_method   VARCHAR(20) NOT NULL,
    coupon_code      VARCHAR(20),
    item_total       NUMERIC(10, 2) NOT NULL,   -- sum(quantity * unit_price)
    discount_amount  NUMERIC(10, 2) NOT NULL,
    delivery_fee     NUMERIC(10, 2) NOT NULL,
    order_value      NUMERIC(10, 2) NOT NULL    -- what the customer paid
);

CREATE TABLE order_items (
    order_id    BIGINT NOT NULL REFERENCES orders (order_id),
    product_id  INTEGER NOT NULL REFERENCES products (product_id),
    quantity    INTEGER NOT NULL,
    unit_price  NUMERIC(10, 2) NOT NULL,
    unit_cost   NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE deliveries (
    order_id          BIGINT PRIMARY KEY REFERENCES orders (order_id),
    rider_id          INTEGER NOT NULL,
    distance_km       NUMERIC(5, 2) NOT NULL,
    promised_minutes  INTEGER NOT NULL,
    actual_minutes    NUMERIC(5, 1) NOT NULL,
    delivered_ts      TIMESTAMP NOT NULL,
    customer_rating   SMALLINT
);

CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_store_ts ON orders (store_id, order_ts);
CREATE INDEX idx_items_product ON order_items (product_id);
