from flask import Flask, request, jsonify
import sqlite3
import requests
import sys
import re

app = Flask(__name__)

# Function to clean html tags
def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

# Function to connect to db
def db_connect():
    conn=sqlite3.connect('products.sqlite')
    return conn

# Routing for POST and GET request (multi)
@app.route('/products', methods=["POST","GET"])
def products():
    # Connecting to db
    conn = db_connect()
    cursor = conn.cursor()

    # GET request method
    if request.method == "GET":
        # Query sql database for all products
        cursor = conn.execute("""
            SELECT * FROM products
            ORDER BY stock DESC, name ASC;
        """)
        products = [
            dict(
                code=row[0],
                name=row[1],
                stock=row[2],
                brand=row[3],
                price=row[4],
                price_promo=row[5],
                description=row[6],
                image_url=row[7].split(', ')
            )
            for row in cursor.fetchall()
        ]

        if products is not None:
            return jsonify(products)

    elif request.method == "POST":
        # Get code from POST request
        code = request.form['code']
        stock = request.form['stock']

        # Scraping data from id.orfilame.com
        url = f"https://id.oriflame.com/system/ajax/pdp/concept?code={code}"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            products = data['products']
        else:
            return f"Error code {res.status_code}"

        name = str()
        price = int()
        price_promo = int()
        image_url = list()
        # Check if product have variant
        if data['isMultiProduct'] == False:
            name = data['name']
            for product in products:
                if product['oldPrice'] == "":
                    price = product['currentPrice']
                    price_promo = 0
                else:
                    price = product['oldPrice']
                    price_promo = product['currentPrice']

                for image in product['images']:
                    image_url.append(str(image['sizes'][2]['url']))

        elif data['isMultiProduct'] == True:
            # Itterating through product variant that match requested code
            for product in products:
                if product['code'] == code:
                    name = f"{data['name']} - {product['shadeName']}"
                    if product['oldPrice'] == "":
                        price = product['currentPrice']
                        price_promo = 0
                    else:
                        price = product['oldPrice']
                        price_promo = product['currentPrice']

                    for image in product['images']:
                        image_url.append(str(image['sizes'][2]['url']))
        brand = data['brandName']
        description = cleanhtml(data['description'])
        image_url = ", ".join(image_url)
        #  image_url = str(image_url)
        print(image_url, file=sys.stdout)

        sql_query = '''
            INSERT INTO products(
                code,name,stock,brand,price,price_promo,
                description,image_url
            )
            VALUES(
                ?,?,?,?,?,?,?,?
            );
        '''

        cursor = cursor.execute(
            sql_query,
            (code,name,stock,brand,price,price_promo,description,image_url)
        )
        conn.commit()
        return f"Products ({code}) {name} has been created successfully."

@app.route('/products/<int:code>', methods=["GET","PUT","DELETE"])
def product(code):
    conn = db_connect()
    cursor = conn.cursor()
    product = None

    if request.method == "GET":
        cursor.execute("SELECT * FROM products WHERE code=?", (code,))
        rows = cursor.fetchall()
        for row in rows:
            product = {
                "code": row[0],
                "name": row[1],
                "stock": row[2],
                "brand": row[3],
                "price": row[4],
                "price_promo": row[5],
                "description": row[6],
                "image_url": row[7].split(', ')
            }
            if product is not None:
                return jsonify(product), 200
            else:
                return "Product with code {code} not found!", 404

    elif request.method == "PUT":
        stock = request.form['stock']

        updated_product = {
            "code": code,
            "stock": stock,
        }

        sql_query = '''
            UPDATE products
            SET stock=?
            WHERE code=?
        '''

        conn.execute(sql_query, (stock,code))
        conn.commit()
        return jsonify(updated_product)

    elif request.method == "DELETE":
        sql_query = '''
            DELETE FROM products WHERE code=?
        '''

        conn.execute(sql_query, (code,))
        conn.commit()

        return f"Product with code: {code} has been deleted.", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
