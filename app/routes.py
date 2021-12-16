from app import app
from flask import render_template, redirect, request, abort
from app.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Product, Order
from app import db
from app.forms import RegistrationForm, AddForm
import stripe
import random

@app.route('/')
@app.route('/index')
@login_required
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/index')
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            return redirect('/login')
        login_user(user, remember=form.remember_me.data)
        return redirect('/index')
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/index')  

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/index')
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect('/index')
    return render_template('register.html', title='Register', form=form)

@app.route('/viewdetails/<productid>', methods=['GET', 'POST'])
@login_required
def viewdetails(productid):
    product = Product.query.get(productid)
    return render_template('details.html', product=product)

@app.route('/order/<product_id>', methods=['POST'])
@login_required
def order(product_id):
    products = Product.query.all()
    product = Product.query.get(product_id)
    if product_id not in products:
        return redirect('/index')

    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                'price_data': {
                    'product_data': {
                        'name': product.name,
                    },
                    'unit_amount': product.price,
                    'currency': 'cad',
                },
                'quantity': 1,
            },
        ],
        payment_method_types=['card'],
        mode='payment',
        success_url=request.host_url + 'success/' + product.id,
        cancel_url=request.host_url + 'cancel',
    )
    return redirect(checkout_session.url)

@app.route('/success/<productpk>', methods=['POST'])
def success(productpk):
    pid = random.randint(100000, 999999)
    p = Product.query.get(productpk)
    o = Order(product=p.name, orderpin=pid)
    db.session.add(o)
    db.session.commit()
    return redirect('/index')

@app.route('/cancel')
def cancel():
    return render_template('cancel.html')

@app.route('/orders/all')
@login_required
def allorders():
    if current_user.email == 'dalia.buckstein@gmail.com':
        orders = Order.query.all()
        return render_template('all.html', orders=orders)
    else:
        return redirect('/index')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def hello():
    form = AddForm()
    if form.validate_on_submit():
        p = Product(name=form.name.data, price=form.price.data, description=form.description.data, ingredients=form.ingredients.data)
        db.session.add(p)
        db.session.commit()
    return render_template('admin.html', form=form)
    

@app.route('/fullfill/<productpk>', methods=['POST'])
@login_required
def fullfill(productpk):
    o = Order.query.get(productpk)
    db.session.delete(o)
    db.session.commit()
    return redirect('/orders/all')