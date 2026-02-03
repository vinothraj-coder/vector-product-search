CREATE DATABASE IF NOT EXISTS product_search;
USE product_search;

CREATE TABLE IF NOT EXISTS products_vectors (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    vector JSON NOT NULL,
    INDEX idx_product_name (product_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;