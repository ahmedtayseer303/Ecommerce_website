# Ecommerce_website
## Before running the app
### Use vscode or any code editor and `pip install` the following:
```
pip install flask
pip install myslqldb
pip install flask-session
pip install werkzeug
```
### Database configuration in app.py file:
1. Import [ecommerce.sql](ecommerce.sql) file in your MySQL DB
   - Open cmd
   - cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"
   - MySQL -u root -p \[database name you have] < "\[location of imported file]\Ecommerce.sql"
     - Ex: mysql -u root -p Ecommerce < "Downloads\ecommerce.sql"
   
2. Change the following configuration with your mysql data in app.py
```
# Configuration for db
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'

# Your mysql passowrd
app.config['MYSQL_PASSWORD'] = '******'

# Configure the name of DB to be connected
app.config['MYSQL_DB'] = 'ecommerce'
```

3. Run flask app `$ flask run` in the direction of app.py file and open the link

## After Running the app
### Using the website as User, you can
In home page:
   - See the available products from merchants to buy or add to cart (with or without login)
   - Search for a product with its name and category (with or without login)
   - Add products to cart
   - Buy after login or register as a user from the home page or buy from your cart

In cart page: 
   - Check your cart from the cart icon and edit number of products needed (with or without login)

In History page:
   - See your history of purchasing products

### Using the website as Merchant, you can
Using app as Merchant, you can
   - Register or login as merchant

In stock page:
   - See your stock products and their details
   - Edit the number of products or delete them in your stock
   - Add new product to your stock

In Sold products page:
   - See the sold products from your stock
   - Show the data of customers bought some of your products
