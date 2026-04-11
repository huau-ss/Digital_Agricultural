import pymysql

conn = pymysql.connect(host='localhost', user='root', password='123456', database='digital_agriculture')
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("SHOW TABLES LIKE 'cleaned_price_data'")
if cursor.fetchone():
    print("表 cleaned_price_data 已存在")
else:
    # 创建表
    sql = """
    CREATE TABLE cleaned_price_data (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        product_id BIGINT NOT NULL,
        date DATE NOT NULL,
        market_name VARCHAR(200) NOT NULL,
        avg_price DECIMAL(10, 4) NOT NULL,
        max_price DECIMAL(10, 4) NULL,
        min_price DECIMAL(10, 4) NULL,
        volume BIGINT NULL,
        source VARCHAR(100) NULL,
        is_outlier TINYINT(1) DEFAULT 0,
        outlier_reason VARCHAR(100) NULL,
        created_at DATETIME(6) NOT NULL,
        INDEX idx_date (date),
        INDEX idx_market_name (market_name),
        INDEX idx_product_date (product_id, date),
        INDEX idx_is_outlier (is_outlier),
        UNIQUE KEY unique_product_market_date (product_id, market_name, date),
        FOREIGN KEY (product_id) REFERENCES agricultural_products(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(sql)
    print("表 cleaned_price_data 创建成功")

conn.close()
