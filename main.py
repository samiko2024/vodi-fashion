from flask import (render_template, url_for, redirect, flash, request, abort,
                   jsonify, Response, send_file, session)
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from __ini__ import create_app, db
from model import User, Product, BlogPost, Video, Comment, Cart, Order, OrderItem, Like
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import joinedload
from functools import wraps
import os
from dotenv import load_dotenv
import hmac
import csv
import hashlib
import requests
import time
from datetime import datetime, date, timedelta
from sqlalchemy import func
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_bootstrap import Bootstrap
from form import (SignUpForm, LonginForm, ForgotPasswordForm,
                  ShopItemForm, CreateBlogForm, VideoUploadForm, ResetPasswordForm, CompleteProfileForm)



load_dotenv()

app = create_app()
Bootstrap(app)
mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'samuelomajali2017@gmail.com'  # use your email
app.config['MAIL_PASSWORD'] = 'fjdczrtpijgvpzlm'  # Gmail App password, not normal one
app.config['MAIL_DEFAULT_SENDER'] = 'samuelomajali2017@gmail.com'



PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY")
PAYSTACK_CALLBACK_URL = os.getenv("PAYSTACK_CALLBACK_URL")
PAYSTACK_WEBHOOK_SECRET = os.getenv("PAYSTACK_WEBHOOK_SECRET")
CURRENCY = os.getenv("CURRENCY", "NGN")


login_manager = LoginManager()
login_manager.init_app(app)





#Create a user_loader Callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function



@app.route('/home')
@login_required
def home():
    all_data = Product.query.limit(8).all()
    return render_template("index.html", data=all_data)




@app.route('/product')
@login_required
def post_product():
    page = request.args.get('page', 1, type=int)
    per_page = 8
    pagination = Product.query.paginate(page=page, per_page=per_page)
    all_data = Product.query.all()
    return render_template("product-post.html", data=all_data,
                           pagination=pagination)



@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query")

    results = Product.query.filter(
        (Product.product_type.ilike(f"%{query}%")) |
        (Product.company.ilike(f"%{query}%"))
    ).all()

    return render_template("product-post.html", data=results, pagination=None)




@app.route('/blog', methods=["GET", "POST"])
@login_required
def blog_page():
    new_post = BlogPost.query.all()
    return render_template("blog.html", post=new_post)

@app.route('/about')
@login_required
def about_us():
    return render_template("about.html")

@app.route('/post-video', methods=["GET", "POST"])
@login_required
def show_video():
    page = request.args.get('page', 1, type=int)
    per_page = 8
    pagination = Product.query.paginate(page=page, per_page=per_page)
    videos = Video.query.all()[:: -1]
    return render_template("post_video.html", videos=videos, pagination=pagination)


@app.route("/video/<int:video_id>")
def view_video(video_id):
    video = Video.query.get_or_404(video_id)
    return render_template("view_video.html", video=video)




@app.route("/video/<int:video_id>/like", methods=["POST"])
@login_required
def like_video(video_id):
    video = Video.query.get_or_404(video_id)

    existing_like = Like.query.filter_by(
        user_id=current_user.id,
        video_id=video.id
    ).first()

    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        video.likes -= 1
    else:
        # Like
        new_like = Like(user_id=current_user.id, video_id=video.id)
        db.session.add(new_like)
        video.likes += 1

    db.session.commit()
    return redirect(url_for("view_video", video_id=video.id))




@app.route('/add_comment/<int:video_id>', methods=['POST'])
@login_required
def add_comment(video_id):
    text = request.form['comment_text']
    if not text.strip():
        flash("Comment cannot be empty", "warning")
        return redirect(url_for('view_video', video_id=video_id))

    comment = Comment(video_id=video_id, user_name='Guest', text=text)
    db.session.add(comment)
    db.session.commit()

    flash("Comment added!", "success")
    return redirect(url_for('view_video', video_id=video_id, comment=comment))


@app.route('/upload-video', methods=['GET','POST'])
@login_required
@admin_only
def upload_video():
    form = VideoUploadForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        contact_url = form.contact_url.data

        file = form.video.data
        if file:
            # Correct upload folder: static/upload-videos
            upload_folder = os.path.join(app.root_path, 'static', 'upload-videos')
            os.makedirs(upload_folder, exist_ok=True)

            # Clean file name
            filename = secure_filename(file.filename)

            # Save file
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # Store ONLY filename in the database
            relative_path = filename  # ✔ correct

            new_video = Video(
                title=title,
                description=description,
                filename=relative_path,
                contact_url=contact_url,
                user_link=current_user.id,
            )
            db.session.add(new_video)
            db.session.commit()

            flash('✅ Video uploaded successfully!', 'success')
            return redirect(url_for('show_video'))
        else:
            flash('⚠️ No file selected.', 'warning')

    else:
        if form.errors:
            print("Form errors:", form.errors)

    return render_template('upload_video.html', form=form, current_user=current_user)






@app.route("/delete-video/<int:video_id>", methods=['GET', 'POST'])
@login_required
@admin_only
def delete_video(video_id):
    video_to_delete = db.get_or_404(Video, video_id)
    db.session.delete(video_to_delete)
    db.session.commit()
    return redirect('/post-video')




# change your password #
@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
    return render_template("profile.html", user=user, orders=orders)



# sign up route
@app.route('/sign-up', methods=["GET", "POST"])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        email = form.email.data
        username = form.username.data
        password1 = form.password1.data
        password2 = form.password2.data
        if password1 == password2:
            new_user = User(
                email = email,
                username = username,
                password = password2,
            )

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('login'))
        else:
            flash('password does not match')
    return render_template("signup.html", form=form, current_user=current_user)


#=======forgot password setup ==========.

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if user:
            token = s.dumps(email, salt='password-reset-salt')
            link = url_for('reset_password', token=token, _external=True)

            msg = Message('Password Reset Request',
                          sender='samuelomajali2017@gmail.com',
                          recipients=[email])
            msg.body = f"Hi, click this link to reset your password:\n{link}\n\nIf you didn't request this, ignore this email."
            mail.send(msg)

            flash('Password reset link has been sent to your email.', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email not found.', 'danger')
    return render_template('forgot_password.html', form=form)



# ========= reset password ==========#
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)
        # token expires in 1 hour
    except:
        flash("The reset link has expired. Request a new one.", "danger")
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(form.password.data)
        db.session.commit()

        flash("Your password has been updated. Login now.", "success")
        return redirect(url_for('login'))

    return render_template("reset_password.html", form=form)





@app.route('/', methods=['GET', 'POST'])
def login():
    form = LonginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash('That email does not exist, signup.')
            return redirect(url_for('sign_up'))
        # Password incorrect
        elif not user.verify_password(password=password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            if current_user.id == 1:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('post_product'))
    return render_template("login.html", form=form, current_user=current_user)

@app.route("/admin/users")
@login_required
def admin_users():
    users = User.query.order_by(User.date_joined.desc()).all()
    total_users = User.query.count()

    return render_template(
        "admin_users.html",
        users=users,
        total_users=total_users
    )



@app.route('/dashboard')
@login_required
@admin_only
def dashboard():
    new_orders = Order.query.filter_by(order_status="processing").count()

    total_orders = Order.query.count()
    total_users = User.query.count()

    total_revenue = db.session.query(
        db.func.sum(Order.total_amount)
    ).scalar() or 0
    return render_template("admin-dashboard.html",
                           new_orders=new_orders,
                           total_orders=total_orders,
                           total_users=total_users,
                           total_revenue=total_revenue
)



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


#============== Adding shop item =====================#
@app.route('/add-shop-items', methods=['GET', 'POST'])
@login_required
@admin_only
def add_shop_items():
    form = ShopItemForm()

    if form.validate_on_submit():

        product_name = form.product_name.data
        product_price = form.product_price.data
        product_type = form.product_type.data
        company = form.company.data
        product_desc = form.product_desc.data
        flash_sale = form.flash_sale.data

        file = form.product_image.data
        if file:
            file.save(os.path.join("static/media", file.filename))
            file_path = os.path.join("static/media", file.filename)

        # ─────────── SAVE PRODUCT DATA ───────────
        product_data = Product(
            product_name=product_name,
            product_price=product_price,
            product_type=product_type,
            company=company,
            product_desc=product_desc,
            flash_sale=flash_sale,
            product_img=file_path
        )

        db.session.add(product_data)
        db.session.commit()
        flash(f"{product_name} added successfully!", "success")

        return redirect(url_for("add_shop_items"))

    return render_template("add_shop_items.html", form=form, current_user=current_user)



@app.route('/shop-item', methods=["GET", "POST"])
@login_required
@admin_only
def shop_items():
    items = Product.query.order_by(Product.date_added).all()
    return render_template("shop-items.html", items=items)





@app.route("/update-items/<int:item_id>", methods=["GET", "POST"])
@login_required
@admin_only
def update_item(item_id):
    form = ShopItemForm()
    item_to_update = Product.query.get(item_id)
    form.product_name.render_kw = {'placeholder': item_to_update.product_name}
    form.product_price.render_kw = {'placeholder': item_to_update.product_price}
    form.product_type.render_kw = {'placeholder': item_to_update.product_type}
    form.company.render_kw = {'placeholder': item_to_update.company}
    form.product_desc.render_kw = {'placeholder': item_to_update.product_desc}
    form.flash_sale.render_kw = {'placeholder': item_to_update.flash_sale}
    if form.validate_on_submit():
        product_name = form.product_name.data
        product_price = form.product_price.data
        product_type = form.product_type.data
        company = form.company.data
        product_desc = form.product_desc.data
        flash_sale = form.flash_sale.data

        file = form.product_image.data
        if file:
            file.save(os.path.join("static/media", file.filename))
            file_path = os.path.join("static/media", file.filename)

        try:
            Product.query.filter_by(id=item_id).update(dict(
                product_name=product_name,
                product_price=product_price,
                product_type=product_type,
                company=company,
                product_desc=product_desc,
                flash_sale=flash_sale,
                product_img=file_path,
            ))
            db.session.commit()
            flash("updated successfully")
            return redirect('/shop-item')
        except Exception as e:
            print('product not updated', e)
            flash('item not updated')
    return render_template("update_item.html", form=form, current_user=current_user)



@app.route("/delete/<int:item_id>", methods=['GET', 'POST'])
@login_required
@admin_only
def delete_items(item_id):
    post_to_delete = db.get_or_404(Product, item_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('shop_items'))



#========= adding Blog post section=========#
@app.route("/add-blog-post", methods=["GET","POST"])
@login_required
@admin_only
def add_blog():
    form = CreateBlogForm()
    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data

        file = form.blog_photo.data
        if file:
            file.save(os.path.join("static/blog", file.filename))
            file_path = os.path.join("static/blog", file.filename)


        new_blog = BlogPost(
            Title=title,
            body=body,
            blog_photo=file_path,
            user_link=current_user.id,
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect('/add-blog-post')

    return render_template("add_blog.html", form=form, current_user=current_user)


@app.route("/delete-blog/<int:item_id>", methods=['GET', 'POST'])
@login_required
@admin_only
def delete_blog(item_id):
    blog_to_delete = db.get_or_404(BlogPost, item_id)
    db.session.delete(blog_to_delete)
    db.session.commit()
    return redirect(url_for('blog_page'))





# ============= cart configuration section =========#
@app.route("/cart", methods=["POST"])
@login_required
def save_cart():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    for item in data:

        existing = Cart.query.filter_by(
            user_link=current_user.id,
            title=item["title"],
            size=item.get("size", "N/A")
        ).first()

        if existing:
            existing.quantity += int(item["quantity"])
        else:
            new_item = Cart(
                user_link=current_user.id,
                title=item["title"],
                price=item["price"],
                quantity=item["quantity"],
                size=item.get("size", "N/A"),
                image=item.get("image", "")
            )
            db.session.add(new_item)

    db.session.commit()
    return jsonify({"message": "Cart updated successfully!"})


@app.route("/cart")
@login_required
def cart():
    items = Cart.query.filter_by(user_link=current_user.id).all()
    total = sum(item.price * item.quantity for item in items)
    return render_template("cart.html", items=items, total=total)



@app.route("/cart/clear", methods=["POST"])
@login_required
def clear_cart():
    Cart.query.filter_by(user_link=current_user.id).delete()
    db.session.commit()
    return jsonify({"message": "Cart cleared!"})


#================= payment gateway configuration===============
def create_order_from_cart_for_user(user):
    cart_items = Cart.query.filter_by(user_link=user.id).all()
    if not cart_items:
        return None

    total_amount = sum(ci.price * ci.quantity for ci in cart_items)

    order = Order(
        user_id=user.id,
        total_amount=total_amount,
        payment_status='pending'
    )
    db.session.add(order)
    db.session.commit()

    for ci in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            title=ci.title,
            price=ci.price,
            quantity=ci.quantity,
            size=ci.size,
            image=ci.image,
            user_link=user.id
        )
        db.session.add(order_item)

    Cart.query.filter_by(user_link=user.id).delete()
    db.session.commit()

    return order




@app.route('/paystack/initialize', methods=['POST'])
@login_required
def paystack_initialize():
    items = Cart.query.filter_by(user_link=current_user.id).all()
    if not items:
        return jsonify({'error': 'Cart is empty'}), 400

    amount = sum(i.price * i.quantity for i in items)
    amount_kobo = int(amount * 100)

    tx_ref = f"psk-{current_user.id}-{int(time.time())}"

    payload = {
        "email": current_user.email,
        "amount": amount_kobo,
        "callback_url": url_for("paystack_callback", _external=True),
        "metadata": {
            "user_id": current_user.id,
            "cart_amount": amount,
            "tx_ref": tx_ref
        }
    }

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
    res = r.json()

    if not res.get("status"):
        return jsonify({"error": res.get("message")}), 400

    return jsonify({"authorization_url": res["data"]["authorization_url"]})




@app.route('/paystack/callback')
@login_required
def paystack_callback():
    reference = request.args.get('reference')
    if not reference:
        flash("Invalid payment reference", "danger")
        return redirect(url_for('cart'))

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}

    verify_url = f"https://api.paystack.co/transaction/verify/{reference}"
    r = requests.get(verify_url, headers=headers)
    res = r.json()

    if not res.get("status"):
        flash("Payment verification failed", "danger")
        return redirect(url_for('cart'))

    data = res["data"]

    if data["status"] == "success":
        user_id = data["metadata"].get("user_id")
        user = User.query.get(user_id)

        order = create_order_from_cart_for_user(user)

        order.payment_status = 'paid'
        order.payment_reference = reference
        order.payment_provider = 'paystack'
        db.session.commit()

        flash("Payment successful!", "success")
        return redirect(url_for("show_order", order_id=order.id))

    flash("Payment was not successful.", "danger")
    return redirect(url_for('cart'))



@app.route('/webhooks/paystack', methods=['POST'])
def paystack_webhook():
    signature = request.headers.get('X-Paystack-Signature')
    body = request.data

    computed = hmac.new(
        PAYSTACK_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha512
    ).hexdigest()

    if computed != signature:
        return abort(403)

    event = request.get_json()

    if event["event"] == "charge.success":
        data = event["data"]
        reference = data["reference"]
        user_id = data["metadata"]["user_id"]

        # Verify again from Paystack
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        verify = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers).json()

        if verify.get("status") and verify["data"]["status"] == "success":
            existing = Order.query.filter_by(payment_reference=reference).first()
            if existing:
                return "ok", 200

            user = User.query.get(user_id)
            order = create_order_from_cart_for_user(user)
            order.payment_status = 'paid'
            order.payment_reference = reference
            order.payment_provider = 'paystack'
            db.session.commit()

    return "ok", 200



#==================Order section================#
@app.route('/my-order/<int:order_id>')
@login_required
def show_order(order_id):
    order = Order.query.get_or_404(order_id)

    # block users from seeing other users' orders
    if order.user_id != current_user.id:
        abort(403)
    if not current_user.phone or not current_user.address:
        return redirect(url_for('complete_profile'))

    return render_template("order_detail.html", order=order)




@app.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
    return render_template('my_orders.html', orders=orders)


@app.route('/admin/orders')
@login_required
@admin_only
def admin_orders():
    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template("admin_order.html", orders=orders)


@app.route('/admin/orders/<int:order_id>')
@login_required
@admin_only
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("admin_order_detail.html", order=order)



@app.route('/admin/orders/<int:order_id>/ship', methods=['POST'])
@login_required
@admin_only
def admin_ship_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.order_status = 'shipped'
    db.session.commit()

    flash("Order marked as shipped", "success")
    return redirect(url_for('admin_order_detail', order_id=order.id))

@app.route('/admin/orders/<int:order_id>/deliver', methods=['POST'])
@login_required
@admin_only
def admin_deliver_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.order_status = 'delivered'
    db.session.commit()

    flash("Order marked as delivered", "success")
    return redirect(url_for('admin_order_detail', order_id=order.id))

@app.route('/admin/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
@admin_only
def admin_cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.order_status = 'cancelled'
    db.session.commit()

    flash("Order cancelled", "danger")
    return redirect(url_for('admin_order_detail', order_id=order.id))

#===========complete profile ==================#
@app.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    form = CompleteProfileForm()

    if form.validate_on_submit():
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.country = form.country.data
        current_user.state = form.state.data
        current_user.note = form.note.data
        db.session.commit()
        return redirect(url_for('my_orders'))

    return render_template('complete_profile.html', form=form)




# =======whatsup configuration ===============#
@app.context_processor
def utility_processor():
    def whatsapp_link(video):
        full_url = request.url_root[:-1] + url_for('view_video', video_id=video.id)
        text = f"Hello, I like this outfit, can you make it for me?: {video.title} ({full_url})"
       # number = "2347045809030"  # change this to your WhatsApp number
        return f"{video.contact_url}?text={text}"
    return dict(whatsapp_link=whatsapp_link)

#===========orders analytic===========#
@app.route('/admin/analytics')
@login_required
@admin_only
def admin_analytics():

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    chart_start = today - timedelta(days=6)

    # ---- SUMMARY CARDS ----
    daily_orders = Order.query.filter(
        func.date(Order.date_created) == today
    ).count()

    daily_revenue = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(
        func.date(Order.date_created) == today,
        Order.payment_status == "paid"
    ).scalar()

    weekly_orders = Order.query.filter(
        Order.date_created >= week_start
    ).count()

    weekly_revenue = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(
        Order.date_created >= week_start,
        Order.payment_status == "paid"
    ).scalar()

    monthly_orders = Order.query.filter(
        Order.date_created >= month_start
    ).count()

    monthly_revenue = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(
        Order.date_created >= month_start,
        Order.payment_status == "paid"
    ).scalar()

    # ---- CHART DATA (LAST 7 DAYS) ----
    stats = db.session.query(
        func.date(Order.date_created),
        func.count(Order.id),
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(
        Order.date_created >= chart_start,
        Order.payment_status == "paid"
    ).group_by(
        func.date(Order.date_created)
    ).all()

    dates = [str(s[0]) for s in stats]  # ✅ FIX
    orders = [s[1] for s in stats]
    revenue = [float(s[2]) for s in stats]

    return render_template(
        "order_analytic.html",
        daily_orders=daily_orders,
        daily_revenue=daily_revenue,
        weekly_orders=weekly_orders,
        weekly_revenue=weekly_revenue,
        monthly_orders=monthly_orders,
        monthly_revenue=monthly_revenue,
        dates=dates,
        orders=orders,
        revenue=revenue
    )

@app.route('/admin/analytics/monthly')
@login_required
@admin_only
def admin_monthly_analytics():

    stats = db.session.query(
        func.strftime('%Y-%m', Order.date_created),  # SQLite-safe
        func.count(Order.id),
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(
        Order.payment_status == "paid"
    ).group_by(
        func.strftime('%Y-%m', Order.date_created)
    ).order_by(
        func.strftime('%Y-%m', Order.date_created)
    ).limit(6).all()

    months = [s[0] for s in stats]
    orders = [s[1] for s in stats]
    revenue = [float(s[2]) for s in stats]

    return render_template(
        "order_analytic.html",
        months=months,
        orders=orders,
        revenue=revenue
    )



@app.route('/admin/analytics/export')
@login_required
@admin_only
def export_analytics():

    orders = Order.query.filter_by(payment_status="paid").all()

    def generate():
        data = []
        header = ["Order ID", "User", "Amount", "Date"]
        data.append(header)

        for o in orders:
            data.append([
                o.id,
                o.user.username,
                o.total_amount,
                o.date_created.strftime("%Y-%m-%d")
            ])

        for row in data:
            yield ",".join(map(str, row)) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics_report.csv"}
    )


if __name__ == '__main__':
    app.run(debug=True)