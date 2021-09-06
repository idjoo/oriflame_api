import sqlite3

conn = sqlite3.connect("products.sqlite")
cursor = conn.cursor()

sql_query = '''
    CREATE TABLE products(
        code INT PRIMARY KEY NOT NULL,
        name TEXT NOT NULL,
        stock INT NOT NULL,
        brand TEXT,
        price INT,
        price_promo INT,
        description TEXT,
        image_url TEXT
    );
'''

cursor.execute(sql_query)
