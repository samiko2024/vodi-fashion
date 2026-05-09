from flask_wtf import FlaskForm
from wtforms import (StringField, SelectField, FloatField, PasswordField,
                     EmailField, BooleanField, SubmitField, TextAreaField, )
from wtforms.validators import DataRequired, Length, EqualTo, URL, Email, ValidationError
from flask_wtf.file import FileField, FileRequired, FileAllowed
import re




class SignUpForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired(), Length(min=2)])
    password1 = PasswordField("Enter Your Password", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField("Confirm your Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Sign Up", render_kw={"class": "my-submit-btn"})


class LonginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Enter Your Password", validators=[DataRequired()])
    submit = SubmitField("Login", render_kw={"class": "my-submit-btn"})

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


class ShopItemForm(FlaskForm):
    product_name = StringField("Name of product", validators=[DataRequired()])
    product_price = FloatField("Product Price", validators=[DataRequired()])
    product_type = StringField("Product Type", validators=[DataRequired()])
    company = StringField("Company", validators=[DataRequired()])
    product_desc = TextAreaField("Product Detail", validators=[DataRequired()])
    product_image = FileField("Product Picture", validators=[FileRequired()])
    flash_sale = BooleanField("Flash Sale")

    add_product = SubmitField("Add Product", render_kw={"class": "btn-primary"})
    update_product = SubmitField("Update Product", render_kw={"class": "btn-primary"})


class CreateBlogForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()],
                        render_kw={"class": " form-control form-control-lg", "placeholder": "Enter blog Title"})
    blog_photo = FileField("Blog Photo", validators=[FileRequired()])
    body = TextAreaField("Blog Content", validators=[DataRequired()],
                       render_kw={"class": "form-control form-control-lg", "placeholder": "Write Blog"})
    post = SubmitField("Post Blog", render_kw={"class": "btn-primary"})



class VideoUploadForm(FlaskForm):
    title = StringField('Video Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    contact_url = StringField('Contact URL', validators=[URL(), DataRequired()])
    video = FileField('Upload Video', validators=[
        FileRequired(),
        FileAllowed(['mp4', 'mov', 'avi', 'mkv'], 'Video files only!')
    ])
    submit = SubmitField('Upload')



def validate_nigeria_phone(form, field):
    phone = field.data.strip()

    pattern = r"^(070|080|081|090|091)\d{8}$"
    if not re.match(pattern, phone):
        raise ValidationError("Enter a valid Nigerian phone number (e.g. 08012345678).")


# ---- State List ----
NIGERIA_STATES = [
    ("Abia", "Abia"), ("Adamawa", "Adamawa"), ("Akwa Ibom", "Akwa Ibom"),
    ("Anambra", "Anambra"), ("Bauchi", "Bauchi"), ("Bayelsa", "Bayelsa"),
    ("Benue", "Benue"), ("Borno", "Borno"), ("Cross River", "Cross River"),
    ("Delta", "Delta"), ("Ebonyi", "Ebonyi"), ("Edo", "Edo"),
    ("Ekiti", "Ekiti"), ("Enugu", "Enugu"), ("Gombe", "Gombe"),
    ("Imo", "Imo"), ("Jigawa", "Jigawa"), ("Kaduna", "Kaduna"),
    ("Kano", "Kano"), ("Katsina", "Katsina"), ("Kebbi", "Kebbi"),
    ("Kogi", "Kogi"), ("Kwara", "Kwara"), ("Lagos", "Lagos"),
    ("Nasarawa", "Nasarawa"), ("Niger", "Niger"), ("Ogun", "Ogun"),
    ("Ondo", "Ondo"), ("Osun", "Osun"), ("Oyo", "Oyo"),
    ("Plateau", "Plateau"), ("Rivers", "Rivers"), ("Sokoto", "Sokoto"),
    ("Taraba", "Taraba"), ("Yobe", "Yobe"), ("Zamfara", "Zamfara"),
    ("FCT", "FCT-Abuja")
]

class CompleteProfileForm(FlaskForm):
    phone = StringField("Phone Number", validators=[DataRequired(), validate_nigeria_phone])
    address = StringField("Delivery Address", validators=[DataRequired(), Length(min=5)])
    state = SelectField("State", choices=NIGERIA_STATES, validators=[DataRequired()])
    country = SelectField("Country", choices=[("Nigeria", "Nigeria"), ("Ghana", "Ghana"), ("Kenya", "Kenya")])
    note = TextAreaField("Delivery Notes (Optional)")
    submit = SubmitField("Save & Continue")