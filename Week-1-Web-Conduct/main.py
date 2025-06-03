import os
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, redirect, url_for, session   
from flask_mysqldb import MySQL
from flask_bootstrap import Bootstrap5
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'wackin'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'week-1-alonde'
app.config['UPLOAD_FOLDER'] = 'static/uploads/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

bootstrap = Bootstrap5(app)
mysql = MySQL(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()  
        cursor.execute('SELECT * FROM tbl_user WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['loggedin'] = True
            session['username'] = user[4]  
            return redirect(url_for('dashboard'))
        else:
            message = 'Incorrect username or password!' 

    return render_template("login.html", message=message)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        birthday = request.form['birthday']
        address = request.form['address']
        username = request.form['username']
        password = request.form['password']

        image = request.files.get('image')
        image_path = None

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path) 
            image_path = filename
        else:
            image_path = None

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tbl_user WHERE username = %s', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            return render_template("register.html", message="Username already exists!")

        cursor.execute(
            'INSERT INTO tbl_user (image_path, name, birthday, address, username, password) VALUES (%s, %s, %s, %s, %s, %s)',
            (image_path, name, birthday, address, username, password)
        )
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template("register.html")

@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    username = session['username']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM tbl_user WHERE username = %s', (username,))
    user = cursor.fetchone()
    cursor.close()

    if user:
        birthdate = user[2]
        age = calculate_age(birthdate)

        user_info = {
            'image_path': user[6] if user[6] else None, 
            'name': user[1],
            'age': age,
            'address': user[3],
        }

        return render_template("dashboard.html", user_info=user_info)

    return redirect(url_for('login'))

def calculate_age(birthday):
    today = datetime.today()
    age = today.year - birthday.year

    if today.month < birthday.month or (today.month == birthday.month and today.day < birthday.day):
        age -= 1

    return age

if __name__ == "__main__":
    app.run(debug=True)
