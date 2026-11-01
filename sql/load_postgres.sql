-- Load the generated CSVs into PostgreSQL (run from the repo root with psql):
--   psql -d quickcommerce -f sql/00_schema.sql -f sql/load_postgres.sql
\copy cities      FROM 'data/raw/cities.csv'      WITH (FORMAT csv, HEADER true)
\copy dark_stores FROM 'data/raw/dark_stores.csv' WITH (FORMAT csv, HEADER true)
\copy customers   FROM 'data/raw/customers.csv'   WITH (FORMAT csv, HEADER true)
\copy products    FROM 'data/raw/products.csv'    WITH (FORMAT csv, HEADER true)
\copy orders      FROM 'data/raw/orders.csv'      WITH (FORMAT csv, HEADER true)
\copy order_items FROM 'data/raw/order_items.csv' WITH (FORMAT csv, HEADER true)
\copy deliveries  FROM 'data/raw/deliveries.csv'  WITH (FORMAT csv, HEADER true)
ANALYZE;
