
from app import (app, render_template,
                 url_for, redirect,
                 request, make_response,
                 send_file, jsonify,
                 flash, session)

from werkzeug.utils import secure_filename

from flask_login import (login_required, login_manager,
                         login_user, logout_user,
                         current_user)

from sqlalchemy import desc

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from app import db, mongo


from app.models import User, Inventory, Quote, Request, Tenant
from app.aux_models import Message

from app.forms import (SubscribeForm, VendorSignUpForm,
                       SignInForm, ResetRequestForm,
                       ResetPasswordForm, SettingsForm,
                       AddProductForm)

from app.utils import (subscribe_user, query_products,
                       vendor_signup_email_alert, request_vendor_email_alert,
                       quote_update_email_alert, quote_received_email_alert,
                       user_confirmation_email, send_password_reset_email,
                       send_web_msg)

import json

from pathlib import Path

import csv
from uuid import uuid4
from datetime import datetime, timedelta

# Some useful variables
date_format = "%Y-%m-%d"

datetime_format = "%Y.%m.%d %H:%M:%S"


@app.route('/search', methods=["GET", "POST"])
def search():

    form = SubscribeForm()

    context = dict(form=form)

    common_entities = SearchKey.query.order_by(desc(SearchKey.counts)).limit(10).all()

    common_searches = [entity.name for entity in common_entities]

    if request.method == "POST":

        keyword = request.form.get('search')

        if keyword:

            keyword = keyword.strip()

        context['query'] = keyword

        return redirect(url_for('render_search_results', query=keyword))

    context["common_searches"] = common_searches
    return render_template("search.html", **context)


@app.route('/product/image/view/<string:product_id>')
def view_image(product_id):

    product = Product.query.get(int(product_id))

    img_src = product.img

    return render_template("view_image.html", img_src=img_src)


@app.route('/product/image/render/<string:product_id>')
def render_image(product_id):

    product = Product.query.get(int(product_id))

    img_src = product.img

    return img_src if img_src else ""


@app.route('/export/results/<string:query>')
def export_data(query):

    data = query_products(query)

    file_name = "data"+str(uuid4())+".csv"

    file = str(Path(app.root_path) / 'cache' / 'user_exports' / file_name)

    headers = ("item name", "barcode", "image",
               "available", "price exw", "origin",
               "amazon url", "item code", "hs code")

    with open(file, mode="w", encoding="utf8") as f:

        writer = csv.writer(f)

        # Write the headers first
        writer.writerow(headers)

        for item in data:

            row = (item.name, item.gtin,
                   item.img, item.is_available,
                   item.price, item.origin,
                   item.amazon_url, item.item_code,
                   item.hs_code)

            writer.writerow(row)

    # Close the csv file when finished writing
    f.close()

    return send_file(file, as_attachment=True, mimetype="text/csv")


@app.route('/', methods=["POST", "GET"])
@app.route('/signin', methods=["GET", "POST"])
def sign_in():

    form = SignInForm()

    if current_user.is_authenticated:

        return redirect(url_for('user_app'))

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(password=form.password.data):

            flash("User account doesn't exist or password is invalid!")

            return redirect(url_for('sign_in'))

        if not user.confirmed:

            flash("User account not confirmed. Please check email!", category="error")

            return redirect(url_for('sign_in'))

        if not user.activated:

            flash("User account is suspended! Please contact your admin", category="danger")

            return redirect(url_for('sign_in'))

        login_user(user, remember=form.remember_me.data)

        return redirect(url_for('user_app'))

    context = dict(form=form)

    return render_template("signin.html", **context)


# passwordless login route
@app.route('/signin/passwordless', methods=["GET", "POST"])
def sign_in_without_password():

    form = SignInForm()

    if current_user.is_authenticated:

        return redirect(url_for('user_app'))

    if request.method == "POST" or form.validate_on_submit():

        # error handling - trim whitespaces and lower the case
        email = form.email.data.strip().lower()

        user = User.query.filter_by(email=email).first()

        full_name = ""

        if user is None:

            flash("User account doesn't exist")

            return redirect(url_for('sign_in'))

        if user:
            full_name = user.user_name
            admin_user = User.query.filter_by(tenant_id=user.tenant_id, is_admin=True).first()

            if not user.activated:

                category = "danger"

                flash(f"Your account is suspended! Please contact your admin {admin_user.email}")

                context = dict(form=form,
                               category=category)

                return render_template("signin_passwordless.html", **context)

        # send an email with link to lgin
        login_msg = "Many thanks!"\
                    " Please click the following link to log into your account. " \
                    "Token expires in 48 hours. So hurry up. If the link is invalid, you can request a new link."

        web_msg = '''
        Many thanks!
        Please check your email with the following link to log into your account. 
        '''

        token = user.generate_confirmation_token()

        email_context = dict(full_name=full_name,
                             msg=login_msg,
                             token=token,
                             email=form.email.data)

        html = render_template("emails/passwordless_email_login.html", **email_context)

        # Send user confirmation email
        try:
            r = user_confirmation_email(html=html,
                                        subject=f"Hi {full_name}, Here's your magic link for login!",
                                        recipients=[user.email])

            print(r)

        except Exception as e:

            print(str(e))

        flash(web_msg)

        return redirect(url_for('sign_in_without_password'))

    context = dict(form=form, category="success")

    return render_template("signin_passwordless.html", **context)


# Create a password-less login route via email
@app.route("/user/account/login/passwordless/<string:token>")
def passwordless_confirm(token):

    s = Serializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token.encode("utf-8"))['confirm']

    except:

        flash('The confirmation link is invalid or has expired.')
        return redirect(url_for('sign_in'))

    user = User.query.get(user_id)
    if user:

        login_user(user)
        flash("Logged in successfully. Many thanks!")
        return redirect(url_for('user_app'))

    error_msg = 'The confirmation link is invalid or has expired. Please request for a magic link again'
    flash(error_msg)
    return redirect(url_for('sign_in_without_password'))


# Logout Route
@app.route('/signout')
def logout():

    logout_user()

    return redirect(url_for('sign_in'))


@app.route("/user/account/confirm/<string:token>")
def confirm(token):

    # If the user isn't authenticated, redirect them to sign in
    if not current_user.is_authenticated:
        return redirect(url_for('sign_in'))

    # If the user is already confirmed, redirect them to the sign in page
    if current_user.confirmed:
        flash("Your account is already confirmed!", category="info")
        return redirect(url_for('sign_in'))

    # If the user hasn't confirmed their account yet, try to confirm it
    if current_user.confirm(token):
        # Activate and confirm the user if confirmed from email
        current_user.activated = True
        current_user.confirmed = True
        db.session.commit()
        flash(
            f"Your account has been confirmed. Many thanks! You can "
            f"now login with your email address {current_user.email}.",
            category="success")

        # Check the Referer header
        referer = request.headers.get('Referer')
        if referer and 'add_user' in referer:
            # Redirect to the sign in page without password if the Referer is 'add_user'
            return redirect(url_for('sign_in_without_password'))

    # If the token isn't valid or expired, or if the referer
    # isn't 'add_user', render the account confirmation page with a failure message
    msg = 'The confirmation link is invalid or has expired.'
    return render_template('account_confirmation.html', msg=msg)


# Route for requesting password reset
@app.route('/request/password/reset', methods=["GET", "POST"])
def request_password_reset():

    form = ResetRequestForm()

    if current_user.is_authenticated:

        # this will lead to the index page by users' roles
        return redirect(url_for('sign_in'))

    if form.validate_on_submit():

        email = form.email.data

        user = User.query.filter_by(email=email).first()

        if user:

            token = user.generate_reset_token()

            alias = user.email or user.contact_person

            msg = '''
            To reset your password, visit the following link.
            If this wasn't you, then simply ignore this email and no changes will be made.
            Otherwise act fast, this link will expire in one hour. 

            '''

            context = dict(token=token,
                           full_name=alias,
                           msg=msg)

            html = render_template("emails/reset_password.html", **context)

            subject = "Password Reset Request - Swiftify"

            send_password_reset_email(html=html,
                                      subject=subject,
                                      user=user)

            flash("A password reset link has been sent to your inbox", "info")

            return redirect(url_for('sign_in'))

        flash("No such user exists, please sign up an account", "error")

        return redirect(url_for('sign_in'))

    return render_template("request_reset.html", form=form)


@app.route('/reset/password/<string:token>', methods=["GET", "POST"])
def reset_password(token):

    form = ResetPasswordForm()

    if current_user.is_authenticated:

        return redirect(url_for('sign_in'))

    user = User.verify_identify_by_token(token=token)

    if user is None:

        flash("This token is expired or the user doesn't exist. ")

        return redirect(url_for('request_password_reset'))

    if form.validate_on_submit() or request.method == "POST":

        password = form.password.data

        user.set_password(password)

        # commit the password change.
        db.session.commit()

        flash('Your password has been changed! You can now log in', 'success')

        return redirect(url_for('sign_in'))

    return render_template("reset_password.html", form=form)


@app.route('/send/confirmation/token')
@login_required
def send_confirm_token():

    referrer = request.headers.get('Referer')

    if current_user.is_authenticated:

        token = current_user.generate_confirmation_token()

        msg = f"Here's your confirmation link again. Click to confirm your account"

        email_context = dict(full_name=current_user.contact_person,
                             msg=msg,
                             token=token)

        html = render_template("emails/account_confirmation.html", **email_context)

        # Send user confirmation email
        try:

            user_confirmation_email(html=html,
                                    subject=f"Here's your confirmation link again @ Swiftify",
                                    recipients=[current_user.email])

        except Exception as e:

            print(str(e))

        flash("Hey! A new confirmation link has been sent to your inbox!")

        return redirect(url_for('sign_in'))

    return redirect(url_for('sign_in'))


@app.route('/account/company/settings', methods=["POST", "GET"])
@login_required
def company_settings():

    form = SettingsForm()

    user = db.session.query(User).get(current_user.id)

    if not user.tenant_id:

        # This user doesn't have a company associated and create one for him
        tenant = Tenant()
        tenant.users.append(user)
        db.session.add(tenant)

        db.session.commit()

    context = dict(form=form)

    form.company_name.data = Tenant.query.get(user.tenant_id).company_name

    form.country.data = user.country
    form.name.data = user.user_name
    form.email.data = user.email

    form.default_currency.data = user.currency

    if user.tenant_id:

        print("This user has a company associated")

        tenant = Tenant.query.get(user.tenant_id)

        # add Tenant instance to html context
        context["tenant"] = tenant

        # showing the business logo
        context["logo"] = tenant.logo

        # if this user has a company associated then add users context for this tenant
        context["users"] = tenant.users

        # fill the current data to the form from user container attribute
        form.city.data = tenant.city
        form.zip_code.data = tenant.zip_code
        form.state_or_province.data = tenant.state_or_province
        form.tax_id.data = tenant.vat_id
        form.eori.data = tenant.eori_id
        form.address.data = tenant.street_n_no

        '''
        Other meta data, retrieve from context
        '''
        form.iban.data = tenant.iban
        form.swift_or_bic_no.data = tenant.swift_code
        form.bank_name.data = tenant.bank_name
        form.bank_address.data = tenant.bank_address
        form.tax_rate1.data = tenant.tax_rate_1
        form.tax_rate2.data = tenant.tax_rate_2

        '''
        technical data from Salesbinder
        '''
        form.salesbinder_subdomain_name.data = tenant.salesbinder_subdomain
        form.salesbinder_api_key.data = tenant.salesbinder_api_key

    if form.validate_on_submit() or request.method == "POST":

        user.user_name = request.form.get("name")

        user.currency = request.form.get("default_currency")

        # Will be saved as a data string into DB
        settings = {'company_name': request.form.get("company_name"),
                    'address': request.form.get("address"),
                    'city': request.form.get("city"),
                    'zip_code': request.form.get("zip_code"),
                    'state_or_province': request.form.get("state_or_province"),
                    'country': request.form.get("country"),
                    'tax_id': request.form.get('tax_id'),
                    'iban': request.form.get('iban'),
                    'swift_code': request.form.get('swift_or_bic_no'),
                    "bank": request.form.get('bank_name'),
                    "bank_address": request.form.get("bank_address"),
                    "tax_rate1": request.form.get('tax_rate1'),
                    "tax_rate2": request.form.get('tax_rate2'),
                    "eori_id": request.form.get('eori'),
                    "salesbinder_subdomain_name": request.form.get("salesbinder_subdomain_name"),
                    "salesbinder_api_key": request.form.get("salesbinder_api_key")
                    }

        # check if a logo has been uploaded
        if form.logo.data:

            file_name = secure_filename(form.logo.data.filename)

            # get the file format by str parsing
            file_format = str(file_name).split('.')[1]

            save_file_name = f'logo_{str(uuid4())}.{file_format}'

            # save the logo data file from the form
            form.logo.data.save(
                str(Path(app.root_path) / 'static' / 'img' / 'tenant_logos' / save_file_name))

            settings['logo'] = save_file_name

        # Update the current tenant's / company's information
        tenant = db.session.query(Tenant).get(user.tenant_id)
        tenant.company_name = settings.get("company_name")
        tenant.street_n_no = settings.get("address")
        tenant.city = settings.get("city")
        tenant.zip_code = settings.get("zip_code")
        tenant.state_or_province = settings.get("state_or_province")
        tenant.country = settings.get("country")
        tenant.logo = settings.get("logo")

        # save financial, taxation and customs data
        tenant.vat_id = settings.get("tax_id")
        tenant.eori_id = settings.get("eori_id")
        tenant.iban = settings.get("iban")
        tenant.swift_code = settings.get("swift_code")
        tenant.bank_name = settings.get("bank")
        tenant.bank_address = settings.get("bank_address")
        tenant.tax_rate_1 = settings.get("tax_rate1")
        tenant.tax_rate_2 = settings.get("tax_rate2")

        # save technical data for intetrating with salesbinder
        tenant.salesbinder_subdomain = settings.get("salesbinder_subdomain_name")
        tenant.salesbinder_api_key = settings.get("salesbinder_api_key")

        # json data text string
        tenant.settings = json.dumps({"setting": settings})

        db.session.commit()

        flash("settings saved and updated", category="success")

        return redirect(url_for('company_settings'))

    return render_template("settings.html", **context)


@app.route('/jsonify/company/settings/<int:user_id>')
@login_required
def jsonify_settings_data(user_id):

    user = User.query.get(int(user_id))

    # disallow other users to view the data
    if current_user.id != user.id:

        return {"error": "access denied"}

    return json.loads(user.container).get('settings')


# route for both vendors and users to view the messages sent to them
@app.route('/view/messages/<string:msg_type>')
@login_required
def view_messages(msg_type):

    '''
    :param msg_type: string: system or user types of messages
    :return: the view route
    '''

    unread_messages = Message.query.filter(
        Message.owner == current_user.email,
        Message.kind == msg_type,
        Message.isRead == False
    ).all()

    read_messages = Message.query.filter(
        Message.owner == current_user.email,
        Message.kind == msg_type,
        Message.isRead == True
    ).all()

    context = dict(unread=unread_messages,
                   read=read_messages,
                   messages=unread_messages + read_messages,
                   title="Alerts Center")

    if msg_type == "user":

        context['title'] = "Messages Center"

    return render_template("view_messages.html", **context)


# mark message as read
@app.route('/mark/message/read', methods=["POST", "GET"])
@login_required
def mark_message_read():

    referrer = request.headers.get('Referer')

    data = request.json

    is_read = data.get('isRead')

    message_id = int(data.get('messageId'))

    message = db.session.query(Message).get(message_id)

    message.isRead = is_read

    db.session.commit()

    return {"messageId": message_id,
            "isRead": is_read}


