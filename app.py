from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
from func import apology

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuration for db
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'

# Your mysql passowrd
app.config['MYSQL_PASSWORD'] = '2927256'

# Configure the name of DB to be connected
app.config['MYSQL_DB'] = 'ecommerce'

# Instantiate obj from mysql
mysql = MySQL(app)


@app.route("/", methods=['GET', 'POST'])
def index():
    cur = mysql.connection.cursor()
    
    # Get method
    if request.method == 'GET':
        resultValue = cur.execute('SELECT * FROM product WHERE prodstockqnt > 0')
        if resultValue > 0:
            products = cur.fetchall()
        else:
            products = []
        cur.close()
        flag = len(products)
        return render_template("home.html", products=products, flag=flag)
    
    # Post request for cart and buy
    pid = request.form.get('pid')
    number = request.form.get('number')
    if not number:
        number = 1
    if not pid or int(number) < 1:
        return apology('Invalid data')
    number = int(number)
    
    # Check if the product id not exists in db
    query = 'SELECT * FROM product WHERE prodid = %s'
    if cur.execute(query, (pid)) <= 0:
        return apology("Invalid product!")
    product = cur.fetchall()        
    quantity = product[0][5]
    if  quantity < number:
        return apology("There is no enough quantity of " + product[0][1])

    # Cart submmit
    if request.form['submit'] == 'cart':
        if session.get("type") and session['type'] == 'user':            
            query = 'SELECT * FROM cart WHERE prodid = %s AND custid = %s'
            if cur.execute(query, (pid, session['user_id'])) > 0:
                cartdb = cur.fetchall()
                if quantity < number+cartdb[0][2]:
                    return apology("The maximum number of " + product[0][1]+ " to have in your cart is "+ str(quantity))
                query = 'UPDATE cart SET orderqnt = %s WHERE custid = %s AND prodid = %s'
                cur.execute(query, (number+cartdb[0][2], session['user_id'], pid))
            else:
                query = 'INSERT INTO cart(custid, prodid, orderqnt) VALUES (%s,%s,%s)'
                cur.execute(query,(session['user_id'], pid, number))
            
            mysql.connection.commit()
        else:
            # First item to be added
            if 'cart' not in session:
                session['cart'] = []
                session['cart'].append((pid,number))
            else:
                # If the product already exists edit
                flag = False
                for i in range(len(session['cart'])):
                    if session['cart'][i][0] == pid:
                        flag = True
                        l = list(session['cart'][i])
                        if quantity < l[1] + number:
                            return apology("The maximum number of " + product[0][1]+ " to have in your cart is "+ str(quantity))
                        l[1] = l[1] + number
                        session['cart'][i] = tuple(l)
                        break
                # New product in the cart
                if flag == False:
                    session['cart'].append((pid,number))
        cur.close()
        return redirect('/cart')
    
    # Buy submmit
    else:
        # login required
        if not session.get("type") or session['type'] != 'user':
            return redirect('/login')
        query = 'UPDATE product SET prodstockqnt = %s WHERE prodid = %s'
        cur.execute(query, (quantity - number, pid))

        query = 'INSERT INTO purchase(custid, prodid, purqnt) VALUES(%s,%s,%s)'
        cur.execute(query, (session['user_id'], pid, number))

        mysql.connection.commit()
        cur.close()
        return redirect('/custHistory')

@app.route('/search')
def search():
    search = request.args.get('search')
    category = request.args.get('category')
    if not (category and search):
        return apology('Invalid Data!')
    # category in...
    search = '%'+ search +'%'
    cur = mysql.connection.cursor()    
    products = []
    if category == 'all':
        if cur.execute('SELECT * FROM product WHERE prodname LIKE %s', {search}) > 0:
            products = cur.fetchall()
    else:
        if cur.execute('SELECT * FROM product WHERE prodname LIKE %s AND category = %s',(search,category)) > 0:
            products = cur.fetchall()
    cur.close()
    flag = len(products)
    return render_template('home.html', products=products, flag=flag)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        atype = request.form.get("type")
        
        if not username or not password or atype not in ['merchant', 'user']:
            return apology("Must provide Valid data")

        cur = mysql.connection.cursor()
        
        # Merchant account
        if atype == 'merchant':
            resultValue = cur.execute('SELECT * FROM seller WHERE username = %(us)s',{'us':username})
            if resultValue <= 0:
                return apology("Invalid username")
            
            # fetch data from cursor as List of tuples
            details = cur.fetchall()
            
            if not check_password_hash(details[0][2], password):
                return apology("Invalid password")
            
            session['user_id'] = details[0][0]
            session['type'] = 'merchant'
            return redirect("/stocks")

        # User account
        resultValue = cur.execute('SELECT * FROM customer WHERE username = %(us)s',{'us':username})
        if resultValue <= 0:
            return apology("Invalid username")
        
        # fetch data from cursor as List of tuples
        details = cur.fetchall()
        
        if not check_password_hash(details[0][3], password):
            return apology("Invalid password")
        
        session['user_id'] = details[0][0]
        session['type'] = 'user'
        
        # Store cart in cart table if exists
        if 'cart' in session:
            for cart in session['cart']:
                query = 'SELECT * FROM cart WHERE prodid = %s AND custid = %s'
                if cur.execute(query, (cart[0], session['user_id'])) > 0:
                    cartdb = cur.fetchall()
                    
                    # Check max number of quantity
                    cur.execute('SELECT * FROM product WHERE prodid = %s',(cart[0]))
                    product = cur.fetchall()
                    if product[0][5] < cart[1]+cartdb[0][2]:
                        orderqnt = product[0][5]
                    else:
                        orderqnt = cart[1]+cartdb[0][2]

                    query = 'UPDATE cart SET orderqnt = %s WHERE custid = %s AND prodid = %s'
                    cur.execute(query, (orderqnt, session['user_id'], cart[0]))
                else:
                    query = 'INSERT INTO cart(custid, prodid, orderqnt) VALUES (%s,%s,%s)'
                    cur.execute(query,(session['user_id'], cart[0], cart[1]))
            mysql.connection.commit()
            del session['cart']
        cur.close()
        return redirect("/")

    # Get request
    return render_template('reg_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        atype = request.form.get("type")
        email = request.form.get("email")
        phone = request.form.get("phoneNumber")
        address = request.form.get("address")

        if not (username and password and email and phone and address) or atype not in ['merchant', 'user']:
            return apology("Invalid Data")

        cur = mysql.connection.cursor()
        
        # Register Merchant account
        if atype == 'merchant':
            if cur.execute("SELECT * FROM seller WHERE username = %(us)s", {'us':username}) > 0:
                return apology("Username Already exists")
            else:
                cur.execute("""INSERT INTO seller(username, hash, sellerphone, 
                                selleremail) VALUES(%s,%s,%s,%s)""", 
                                (username, generate_password_hash(password), phone, email))

            mysql.connection.commit()
            session['user_id'] = cur.lastrowid
            session['type'] = 'merchant'
            cur.close()
            return redirect("/stocks")

        # Regiter user account
        if cur.execute("SELECT * FROM customer WHERE username = %(us)s", {'us':username}) > 0:
            return apology("Username Already exists")
        else:
            cur.execute("""INSERT INTO customer(username, hash, custphone, 
                            custemail, custaddress)VALUES(%s,%s,%s,%s,%s)""", 
                            (username, generate_password_hash(password), phone, email, address))
        
        mysql.connection.commit()
        session['user_id'] = cur.lastrowid
        session['type'] = 'user'
        
        # Store cart data if exists
        if 'cart' in session:
            for cart in session['cart']:
                query ='INSERT INTO cart(custid, prodid, orderqnt) VALUES(%s,%s,%s)'
                cur.execute(query,(session['user_id'], cart[0], cart[1]))
        mysql.connection.commit()
        cur.close()
        del session['cart']
        return redirect('/')

    return render_template('reg_login.html')

@app.route('/logout')
def logout():
    session['user_id'] = None
    session['type'] = None
    return redirect('/login')

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        pid = request.form.get('pid')
        number = request.form.get('number')

        if not (pid and number) or int(number) < 0:
            return apology('Invalid Data!')
        number = int(number)
        
        # Check for wrong product id
        query = 'SELECT * FROM product WHERE prodid = %s'
        if cur.execute(query, {pid}) <= 0:
            return apology('Invalid Data!')
        
        product = cur.fetchall()
            
        if product[0][5] < number:
            return apology("The maximum available quantity of " + product[0][1]+ " to have in your cart is "+ str(product[0][5]))
        
        # For loged in user
        if session.get('type') and session['type'] == 'user':
            if number == 0:
                query = 'DELETE FROM cart WHERE custid = %s AND prodid = %s'
                cur.execute(query, (session['user_id'], pid))
            else:
                query = 'UPDATE cart SET orderqnt = %s WHERE custid = %s AND prodid = %s'
                cur.execute(query, (number, session['user_id'], pid))
            mysql.connection.commit()

        # For non loged in
        else:
            if 'cart' in session:
                for i in range(len(session['cart'])):
                    if session['cart'][i][0] == pid:
                        # Check to delete the product or update the quantity
                        if number == 0:
                            session['cart'].pop(i)
                        else:
                            session['cart'][i] = (pid, number)
                        break
        cur.close()
        return redirect('/cart')
        
    # GET method
    products = []
    totalprice = 0
    if session.get("type") and session["type"] == 'user':
        
        # First update if there is any change in stock quantities
        query = 'update cart c, product p set orderqnt = prodstockqnt where orderqnt > prodstockqnt and p.prodid=c.prodid and custid = %s'
        cur.execute(query, {session['user_id']})
        mysql.connection.commit()

        query = 'SELECT * FROM product p, cart ct, customer c WHERE ct.custid=c.custid AND p.prodid=ct.prodid AND c.custid = %(cid)s'
        resultValue = cur.execute(query, {'cid': session['user_id']})
        if resultValue > 0:
            products = cur.fetchall()
        
        query = 'SELECT SUM(orderqnt*prodprice) FROM product p, cart ct, customer c WHERE ct.custid=c.custid AND p.prodid=ct.prodid AND c.custid = %(cid)s'
        cur.execute(query,{'cid': session['user_id']})
        total = cur.fetchall()
        if total[0][0]:
            totalprice = total[0][0]
    else:
        if 'cart' in session:
            query = 'SELECT * FROM product WHERE prodid = %(id)s'
            totalprice = 0
            for cart in session['cart']:
                cur.execute(query, {'id': cart[0]})
                details = cur.fetchall()
                
                # Append the qunatity
                l = list(details[0])
                l.append(cart[1])
                details = tuple(l)
                products.append(details)
                
                totalprice = totalprice + (cart[1] * l[4])
    
    cur.close()
    return render_template("cart.html", products=products, totalprice=totalprice)

@app.route('/stocks', methods=['GET', 'POST'])
def stocks():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        pid = request.form.get('pid')
        submit = request.form.get('submit')
        
        if not (submit and pid):
            return apology('Invalid Data!')
        if cur.execute('SELECT * FROM product WHERE prodid = %s', {pid}) <= 0:
            return apology('Invalid Data!')
        
        if submit == 'editqnt':
            number = request.form.get('number')
            if not number or int(number) < 0:
                return apology('Invalid Data!')
            int(number)
            query = 'UPDATE product SET prodstockqnt = %s WHERE prodid = %s'
            cur.execute(query, (number, pid))
        else:
            query = 'DELETE FROM product WHERE prodid = %s AND sellerid = %s'
            cur.execute(query,(pid, session['user_id']))
 
        mysql.connection.commit()
        cur.close()
        return redirect('/stocks')

    # Get request
    if not session.get("type") or session['type'] != 'merchant':
        return redirect("/login")
    products = []
    query = 'select * from product where sellerid = %s order by prodstockqnt desc'
    if cur.execute(query, {session['user_id']}) > 0:
        products = cur.fetchall()
    return render_template('stocks.html', products=products)


@app.route('/add', methods=['POST'])
def add():
    name = request.form.get('name')
    description = request.form.get("description")
    price = request.form.get('price')
    category = request.form.get('category')
    image = request.form.get('image')
    quantity = request.form.get('quantity')

    if not (name and description and price and image and quantity) or int(quantity) < 1 or int(price) < 0:
        return apology('Invalid data')
    quantity = int(quantity)
    price = int(price)

    cur = mysql.connection.cursor()
    query = 'INSERT INTO product(prodname, proddescription, prodprice, category, prodStockQnt, imageurl, sellerid) VALUES(%s,%s,%s,%s,%s,%s,%s)'
    cur.execute(query,(name, description, price, category, quantity, image, session['user_id']))
    mysql.connection.commit()
    cur.close()
    return redirect('/stocks')

@app.route('/buy_cart', methods=['POST'])
def buy_cart():
    if not session.get('type') or session['type'] != 'user':
        return redirect('/login')
    cur = mysql.connection.cursor()
    query = 'SELECT * FROM cart WHERE custid=%s'
    if cur.execute(query, {session['user_id']}) > 0:
        cartdb = cur.fetchall()
        
        # Update quntity in stock
        query = 'UPDATE product SET prodstockqnt = prodstockqnt - %s WHERE prodid = %s'
        for cart in cartdb:
            cur.execute(query, (cart[2],cart[1]))

        # Inser in purchase history
        query = 'INSERT INTO purchase(custid, prodid, purqnt) SELECT * FROM cart where custid = %s'
        cur.execute(query, {session['user_id']})
        
        # Delete bought products from cart
        query = 'DELETE FROM cart WHERE custid = %s'
        cur.execute(query, {session['user_id']})
        mysql.connection.commit()
    cur.close()
    return redirect('/custHistory')

@app.route('/custHistory')
def custHistory():

    # Login required
    if not session.get("type") or session["type"] != 'user':
        return redirect('/login')

    cur = mysql.connection.cursor()
    query = 'SELECT * FROM product p, purchase pur WHERE pur.prodid = p.prodid AND custid = %s'
    products = []
    if cur.execute(query, {session['user_id']}) > 0:
        products = cur.fetchall()
    return render_template('custHistory.html', products=products)

@app.route('/sellerHistory', methods=['GET', 'POST'])
def sellerHistory():

    # Login required
    if not session.get("type") or session["type"] != 'merchant':
        return redirect('/login')

    # Post request
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        custid = request.form.get('custid')
        if not custid or cur.execute('SELECT * FROM customer WHERE custid = %s',{custid}) <= 0:
            return apology('Invalid Data')
        customer = cur.fetchall()
        return render_template('buyer.html', customer=customer)

    # GET reqest    
    query = 'SELECT * FROM product p, purchase pur WHERE pur.prodid = p.prodid AND sellerid = %s'
    products = []
    if cur.execute(query, {session['user_id']}) > 0:
        products = cur.fetchall()
    return render_template('sellerHistory.html', products=products)

if __name__ == "__main__":
    app.run(debug=True)
