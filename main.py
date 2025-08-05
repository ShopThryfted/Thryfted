from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import stripe
import os
import json
import csv
from flask_mail import Mail, Message as MailMessage
import pytz

print("Saving to:", os.path.abspath('survey_responses.csv'))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-dont-use')

app.secret_key = app.config['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///messages.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_USERNAME')
)

utc_time = datetime.utcnow()
eastern = pytz.timezone('America/New_York')
est_time = utc_time.replace(tzinfo=pytz.utc).astimezone(eastern)
timestamp_str = est_time.strftime('%Y-%m-%d %H:%M:%S %Z')

mail = Mail(app)

db = SQLAlchemy(app)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(100))
    category = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def __init__(self, name, email, company, category, message):
        self.name = name
        self.email = email
        self.company = company
        self.category = category
        self.message = message

@app.route('/')
def root():
    if session.get('survey_completed'):
        return redirect(url_for('home'))
    return redirect(url_for('survey'))

SITE_VIEWS_FILE = 'site_views.json'

def load_site_views():
    if os.path.exists(SITE_VIEWS_FILE):
        with open(SITE_VIEWS_FILE, 'r') as f:
            return json.load(f).get('views', 0)
    return 0

def increment_site_views():
    views = load_site_views() + 1
    with open(SITE_VIEWS_FILE, 'w') as f:
        json.dump({'views': views}, f)
    print(f"Site viewed: {views} times")
    return views

REVENUE_FILE = 'revenue.json'

def load_revenue():
    if os.path.exists(REVENUE_FILE):
        with open(REVENUE_FILE, 'r') as f:
            data = json.load(f)
            return data.get('total', 0.0)
    return 0.0

def add_revenue(amount):
    current = load_revenue()
    new_total = current + amount
    with open(REVENUE_FILE, 'w') as f:
        json.dump({'total': new_total}, f)

@app.route('/home')
def home():
    increment_site_views()
    featured_products = PRODUCTS[:3]
    return render_template('home.html', products=featured_products)

PRODUCTS = [
    {
        'id': 1,
        'name': 'Nike Air Force 1',
        'brand': 'Nike',
        'original_price': 90.00,
        'price': 38.00,
        'image': 'images/nike air force 1.png',
        'description': 'Iconic all-white leather sneakers. Lightly worn, still crisp. Streetwear essential.',
        'category': 'shoes',
        'gender': 'unisex'
    },
    {
        'id': 2,
        'name': 'Vintage Tommy Hilfiger Hoodie',
        'brand': 'Tommy Hilfiger',
        'original_price': 70.00,
        'price': 22.00,
        'image': 'images/tommyhilfiger.jpg',
        'description': 'Y2K-style oversized hoodie with bold logo. Cozy fit and perfect for layering.',
        'category': 'tops',
        'gender': 'unisex'
    },
    {
        'id': 3,
        'name': 'Relaxed Jeans - 1996 D-Sire - Medium Blue',
        'brand': 'DIESEL',
        'original_price': 125.00,
        'price': 55.00,
        'image': 'images/diesel jeans.jpg',
        'description': 'Medium-wash vintage fit with natural fading. 90s-inspired wide leg.',
        'category': 'bottoms',
        'gender': 'women'
    },
    {
        'id': 4,
        'name': 'DICE HOODIE PIGMENT DYED',
        'brand': 'Stüssy',
        'original_price': 105.00,
        'price': 47.00,
        'image': 'images/stuussy.png',
        'description': 'Washed cream hoodie with dice graphic. Relaxed fit and heavy feel. Retro skater vibes.',
        'category': 'tops',
        'gender': 'men'
    },
    {
        'id': 5,
        'name': 'Classic Logo Blowout Bootcut Jeans',
        'brand': 'Miss Me',
        'original_price': 103.00,
        'price': 42.50,
        'image': 'images/missme.png',
        'description': 'Low-rise bootcut jeans with rhinestone back pockets. Real early-2000s energy.',
        'category': 'outerwear',
        'gender': 'unisex'
    },
    {
        'id': 6,
        'name': 'Vintage Nike Varsity Jacket',
        'brand': 'Brandy Melville',
        'original_price': 120.00,
        'price': 48.00,
        'image': 'images/nike varsity.png',
        'description': 'Two-tone varsity jacket with embroidered swoosh. Heavyweight and bold.',
        'category': 'tops',
        'gender': 'women'
    }
]

FOUNDERS = [
    {
        'name': 'Keziah Letsa',
        'role': 'Co-Founder & Business Affiliate',
        'bio': 'Rising Sophomore passionate about making style accessible to all communities.',
        'image': 'images/keziah.jpeg'
    },
    {
        'name': 'Yasmin Folarin',
        'role': 'Co-Founder & Business Affiliate',
        'bio': 'Rising sophomore in Business passionate about connecting brands with underserved communities.',
        'image': 'images/Yasmin (1).jpeg'
    },
    {
        'name': 'Jaheem Beck',
        'role': 'Co-Founder & Product Development',
        'bio': 'Rising sophomore that has an interest in programming',
        'image': 'images/Jaheem.jpg'
    },
    {
        'name': 'Tochi Ugboajah',
        'role': 'Co-Founder & Product Development',
        'bio': 'Rising sophomore passionate about Programming, and focused on building platforms that create social impact.',
        'image': 'images/Tochi.jpg'
    }
]

@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        print("Survey POST received ✅")
        style = request.form.get('style')
        size = request.form.get('size')
        brands = request.form.get('brands')
        name = request.form.get('name')
        email = request.form.get('email')

        file_path = 'survey_responses.csv'
        file_exists = os.path.isfile(file_path)

        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['Style', 'Size', 'Brands Interested', 'Name', 'Email', 'Timestamp'])

            # writer.writerow(["test-style", "test-size", "yes", "test name", "test@email.com", datetime.utcnow()])
            print("Received survey:", style, size, brands, name, email)
            writer.writerow([style, size, brands, name, email, timestamp_str])

        session['survey_completed'] = True
        flash("Thanks for completing the survey!", "success")
        return redirect(url_for('home'))

    return render_template('survey.html')

@app.route('/retake_survey')
def retake_survey():
    session.pop('survey_completed', None)
    flash('You can now retake the survey.', 'info')
    return redirect(url_for('survey'))

SHARE_COUNT_FILE = 'share_count.json'

def load_share_count():
    if os.path.exists(SHARE_COUNT_FILE):
        with open(SHARE_COUNT_FILE, 'r') as f:
            return json.load(f).get('count', 0)
    return 0

def increment_share_count():
    count = load_share_count() + 1
    with open(SHARE_COUNT_FILE, 'w') as f:
        json.dump({'count': count}, f)
    return count

@app.route('/share_count', methods=['POST'])
def share_count_route():
    count = increment_share_count()
    print(f"Shared {count} times")
    return '', 204

def get_cart():
    return session.get('cart', {})

def add_to_cart(product_id, quantity=1):
    cart = get_cart()
    if str(product_id) in cart:
        cart[str(product_id)] += quantity
    else:
        cart[str(product_id)] = quantity
    session['cart'] = cart

def remove_from_cart(product_id):
    cart = get_cart()
    if str(product_id) in cart:
        del cart[str(product_id)]
    session['cart'] = cart

def get_cart_items():
    cart = get_cart()
    items = []
    total = 0
    for product_id, quantity in cart.items():
        product = next((p for p in PRODUCTS if p['id'] == int(product_id)), None)
        if product:
            item = {
                'product': product,
                'quantity': quantity,
                'subtotal': product['price'] * quantity
            }
            items.append(item)
            total += item['subtotal']
    return items, total


@app.route('/shop')
def shop():
    return render_template('shop.html', products=PRODUCTS)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('shop'))
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart_route(product_id):
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if product:
        add_to_cart(product_id)
        flash(f'{product["name"]} added to cart!', 'success')
    return redirect(request.referrer or url_for('shop'))

@app.route('/cart')
def cart():
    items, total = get_cart_items()
    return render_template('cart.html', items=items, total=total, stripe_key=STRIPE_PUBLISHABLE_KEY)

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart_route(product_id):
    remove_from_cart(product_id)
    return redirect(url_for('cart'))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    cart = get_cart()
    for product_id in list(cart.keys()):
        quantity = int(request.form.get(f'quantity_{product_id}', 0))
        if quantity > 0:
            cart[product_id] = quantity
        else:
            del cart[product_id]
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/create_checkout_session', methods=['POST'])
def create_checkout_session():
    try:
        items, total = get_cart_items()
        if not items:
            flash('Your cart is empty!', 'error')
            return redirect(url_for('cart'))

        line_items = []
        for item in items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item['product']['name'],
                        'description': item['product']['description']
                    },
                    'unit_amount': int(item['product']['price'] * 100),
                },
                'quantity': item['quantity'],
            })

        session_stripe = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('payment_success', _external=True),
            cancel_url=url_for('cart', _external=True),
        )

        return redirect(session_stripe.url, code=303)

    except Exception as e:
        flash('Error creating checkout session. Please try again.', 'error')
        return redirect(url_for('cart'))

@app.route('/payment_success')
def payment_success():
    _, total = get_cart_items()
    add_revenue(total)
    session['cart'] = {}
    return render_template('payment_success.html')

@app.route('/stripe_webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, 'whsec_your_webhook_secret'
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(f"Payment successful: {session['id']}")

    return 'Success', 200

def format_est(timestamp):
    if timestamp is None:
        return ''
    est = pytz.timezone('America/New_York')
    utc = timestamp.replace(tzinfo=pytz.utc)
    return utc.astimezone(est).strftime('%m/%d/%Y at %I:%M %p %Z')

@app.route('/partners', methods=['GET', 'POST'])
def partners():
    if request.method == 'POST':
        name=request.form.get('name')
        email=request.form.get('email')
        company=request.form.get('company', '')
        category=request.form.get('category')
        message=request.form.get('message')

        try:
            message_obj = ContactMessage(name, email, company, category, message)
            db.session.add(message_obj)
            db.session.commit()
            flash('Thank you for your message! We\'ll get back to you soon.', 'success')
            return redirect(url_for('partners'))
        except Exception as e:
            db.session.rollback()
            print("Form submission error:", e)
            flash('Sorry, there was an error sending your message. Please try again.', 'error')

    company_info = {
        'email': os.getenv('COMPANY_EMAIL', 'shopthryfted@gmail.com'),
        'instagram': os.getenv('COMPANY_INSTAGRAM', '@shop.thryfted'),
        'phone': os.getenv('COMPANY_PHONE', '+1 (929) 459-8466')
    }

    return render_template('partners.html', company_info=company_info)


@app.route('/about')
def about():
    return render_template('about.html', founders=FOUNDERS)

# Admin Routes (Secret)
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        correct_password = os.getenv('ADMIN_PASSWORD')

        if password == correct_password:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_messages'))

        flash('Incorrect password', 'error')

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/messages')
def admin_messages():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    messages = ContactMessage.query.order_by(ContactMessage.timestamp.desc()).all()
    site_views = load_site_views()
    share_count = load_share_count()
    revenue = load_revenue()
    return render_template('admin_messages.html', messages=messages, site_views=site_views, share_count=share_count, revenue=revenue)

@app.route('/admin/mark_read/<int:message_id>')
def mark_read(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    return redirect(url_for('admin_messages'))

@app.route('/admin/delete_message/<int:message_id>')
def delete_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted successfully.', 'success')
    return redirect(url_for('admin_messages'))

@app.route('/admin/reply/<int:message_id>', methods=['GET', 'POST'])
def admin_reply(message_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    msg = ContactMessage.query.get_or_404(message_id)

    if request.method == 'POST':
        subject = request.form.get('subject')
        body = request.form.get('body')

        if not subject or not body:
            flash('Subject and message body are required.', 'error')
            return redirect(url_for('admin_reply', message_id=message_id))

        try:
            email = MailMessage(
                subject=subject,
                recipients=[msg.email],
                body=body
            )
            mail.send(email)
            flash('Reply sent successfully!', 'success')
            return redirect(url_for('admin_messages'))
        except Exception as e:
            flash(f'Failed to send email: {e}', 'error')

    default_subject = f"Re: {msg.category.title()} Inquiry"
    default_body = f"Hi {msg.name},\n\nThank you for reaching out to Thryfted Archive.\n\n"

    return render_template('admin_reply.html', message=msg, default_subject=default_subject, default_body=default_body)



with app.app_context():
    db.create_all()

app.jinja_env.globals.update(format_est=format_est)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)