import pymysql

conn = pymysql.connect(host='localhost', user='root', password='123456', database='digital_agriculture')
cursor = conn.cursor()

# 总记录数
cursor.execute('SELECT COUNT(*) FROM price_history')
print(f'总记录数: {cursor.fetchone()[0]}')

# 日期范围
cursor.execute('SELECT MIN(date), MAX(date) FROM price_history')
date_range = cursor.fetchone()
print(f'日期范围: {date_range[0]} ~ {date_range[1]}')

# 查看样本数据
cursor.execute('SELECT id, product_id, market_name, date, avg_price, remarks FROM price_history LIMIT 5')
print('\n样本数据:')
for row in cursor.fetchall():
    print(f'  ID={row[0]}, 产品ID={row[1]}, 市场={row[2]}, 日期={row[3]}, 价格={row[4]}, 备注={row[5]}')

# 异常值标记
cursor.execute("SELECT COUNT(*) FROM price_history WHERE remarks = '异常值'")
print(f'\n标记为异常的记录数: {cursor.fetchone()[0]}')

# 按产品统计
cursor.execute('''
    SELECT p.name, COUNT(*) as cnt
    FROM price_history h
    JOIN agricultural_products p ON h.product_id = p.id
    GROUP BY p.name
    ORDER BY cnt DESC
    LIMIT 10
''')
print('\n各产品记录数:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}条')

conn.close()
