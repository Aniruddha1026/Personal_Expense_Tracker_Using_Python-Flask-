from flask import Flask,request,render_template,redirect,url_for,session,flash
import sqlite3
from werkzeug.security import check_password_hash,generate_password_hash
from datetime import datetime


app=Flask(__name__)
app.secret_key="expense_tracker"


def get_db_connection():
    conn = sqlite3.connect("expense_tracker.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def root():
    return redirect(url_for('login'))


@app.route('/login',methods=["GET","POST"])
def login():
    if request.method=="POST":
        conn=get_db_connection()
        cursor=conn.cursor()
        
        username=request.form['username']
        password=request.form['password']
        if not username or not password:
            return render_template("login.html",msg="Please fill all the fields")

        cursor.execute("SELECT * FROM signup WHERE username=?",(username,))
        user=cursor.fetchone()
        conn.close()
        if user:
            if check_password_hash(user['password'],password):
                session['username']=username
                flash("You have been logged in successfully.")
                return redirect(url_for('home'))
            else:
                return render_template('login.html',msg="Incorrect Password")
        else:
            return render_template("login.html",msg="Username does not exist")


    return render_template('login.html')

@app.route("/logout")
def logout():
    session.pop('username',None)
    flash("You have been logged out.")
    return redirect(url_for('login'))


@app.route('/register',methods=["GET","POST"])
def register():
    if request.method=="POST":
        conn=get_db_connection()
        cursor=conn.cursor()
       

        username=request.form['username']
        password=request.form['password']
        if not username or not password:
            return render_template("register.html",msg="Please fill all the fields")

        cursor.execute("SELECT * FROM signup WHERE username=?",(username,))
        user=cursor.fetchone()
        if user:
            conn.close()
            return render_template("register.html",msg="Username already exists")
        else:
            hashed_password=generate_password_hash(password)
            cursor.execute("INSERT INTO signup (username,password) VALUES (?,?)",(username,hashed_password,))
            conn.commit()
            conn.close()
            flash("Account created successfully. Please log in.")
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/home',methods=["GET","POST"])
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username=session['username']
    conn=get_db_connection()
    cursor=conn.cursor()

    #recent expenses
    cursor.execute("SELECT * FROM expense WHERE username=? ORDER BY date DESC LIMIT 5",(username,))
    recent_expenses=cursor.fetchall()

    #total expense of the current month
    now=datetime.now()
    month_name=now.strftime('%B')
    month_number=now.strftime('%m')
    year=now.strftime('%Y')
    cursor.execute("SELECT SUM(amount) FROM expense WHERE username=? AND strftime('%m',date)=? AND strftime('%Y',date)=?",(username,month_number,year,))
    monthly_total=cursor.fetchone()[0] or 0

    #last month expense vs current month expense
    if int(month_number)==1:
        last_month=12
        last_year=int(year)-1
    elif int(month_number)>1 and int(month_number)<13:
        last_month=int(month_number)-1
        last_year=int(year)
    last_month_padded = f"{last_month:02d}"
    cursor.execute("SELECT SUM(amount) FROM expense WHERE username=? AND strftime('%m',date)=? AND strftime('%Y',date)=?",(username,last_month_padded,str(last_year),))
    last_month_total=cursor.fetchone()[0] or 0
    if last_month_total==0:
        if monthly_total==0:
            status="No change"
            percentage_change=0
        else:
            status="increased"
            percentage_change=100
    else:
        difference=monthly_total-last_month_total
        percentage_change=(difference/last_month_total)*100
        percentage_change=abs(round(percentage_change,2))
        if percentage_change>100:
            percentage_change=100
        if difference>0:
            status="increased"
        elif difference<0:
            status="decreased"
        else:
            status="No Change"
    
    conn.close()
    return render_template(
        "home.html",
        username=session['username'],
        recent_expenses=recent_expenses,
        monthly_total=monthly_total,
        month_name=month_name,year=year,
        last_month_total=last_month_total,
        percentage_change=percentage_change,
        status=status
        )

@app.route('/add_expense',methods=["GET","POST"])
def add_expense():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method=="POST":
        conn=get_db_connection()
        cursor=conn.cursor()
        
        username=session['username']
        title=request.form['title']
        amount=request.form['amount']
        date=request.form['date']

        if not title or not amount or not date:
            return render_template("add_expense.html",msg="Please fill all the fields")
        
        cursor.execute("INSERT INTO expense (username,title,amount,date) VALUES (?,?,?,?)",(username,title,amount,date,))
        conn.commit()
        conn.close()
        flash("Expense added succesfully")
        return redirect(url_for('home'))
    return render_template("add_expense.html")

@app.route('/view_expense',methods=["GET","POST"])
def view_expense():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn=get_db_connection()
    cursor=conn.cursor()
    username=session['username']
    if request.method=="POST":
        title=request.form['title']
        start_date=request.form['start_date']
        end_date=request.form['end_date']
        min_amount=request.form['min_amount']
        max_amount=request.form['max_amount']
        query="SELECT * FROM expense WHERE username=?"
        params=[username]
        if title:
            query=query+" AND title LIKE ?"
            params.append(f'%{title}%')
        if start_date:
            query=query+" AND date >= ?"
            params.append(start_date)
        if end_date:
            query=query+" AND date <= ?"
            params.append(end_date)
        if min_amount:
            query=query+" AND amount >= ?"
            params.append(min_amount)
        if max_amount:
            query=query+" AND amount <= ?"
            params.append(max_amount)
        cursor.execute(query,tuple(params))
        expenses=cursor.fetchall()
    else:
        cursor.execute("SELECT * FROM expense WHERE username=?",(username,))
        expenses=cursor.fetchall()
    conn.close()
    return render_template('view_expense.html',expenses=expenses)

@app.route('/delete_expense/<int:id>')
def delete_expense(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("DELETE FROM expense WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_expense'))

@app.route('/edit_expense/<int:id>',methods=["GET","POST"])
def edit_expense(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM expense WHERE id=?",(id,))
    existed_expense=cursor.fetchone()
    if request.method=="POST":
        username=session['username']
        title=request.form['title']
        amount=request.form['amount']
        date=request.form['date']
        if not title or not amount or not date:
            return render_template("edit_expense.html",existed_expense=existed_expense,msg="Please fill all the fields")
        
        cursor.execute("UPDATE expense SET title=?,amount=?,date=? WHERE id=? AND username=?",(title,amount,date,id,username,))
        conn.commit()
        conn.close()
        flash("Updated Successfully")
        return redirect(url_for('view_expense'))
    conn.close()
    return render_template("edit_expense.html",existed_expense=existed_expense)

