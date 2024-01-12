from app import (app, render_template,
                 url_for, redirect,
                 request, make_response,
                 send_file, jsonify,
                 flash, session, abort)
from pprint import pprint

from werkzeug.utils import secure_filename

from flask_login import (login_required, login_manager,
                         login_user, logout_user,
                         current_user)

from flask_babel import format_datetime, format_date, format_decimal, format_currency

from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from app import db, mongo

from app.models import (Inventory, Quote, PO, Request,
                        Warehouse, Shipment, User,
                        Tenant, Supplier, Role, inventory_supplier, Activity)

from app.models import User


from app.forms import (UserSignUpForm, SendEmailForm,
                       SendInvoiceForm, AddAccountForm,
                       RejectQuoteForm, AddProductForm,
                       AddWarehouseForm, DataRequired,
                       SelectMultipleField, SelectField,
                       SendPOForm, SubmitField,
                       CreatePOForm, UserForm)

from app.utils import (user_confirmation_email,
                       send_quote_or_request_via_email,
                       quote_rejection_vendor_email_alert, email_invoice,
                       html2pdf, get_image_file_as_base64_data,
                       query_products, RedisCache,
                       request_vendor_email_alert, quote_update_email_alert,
                       quote_received_email_alert, send_web_msg, JsonCache,
                       return_currencies, get_currency_symbol,
                       po_messenger)

import json

from pathlib import Path

import csv
from uuid import uuid4
from datetime import datetime
import io
import csv

import os
from os import remove
from functools import wraps
from config import Config
import pusher

pusher_client = pusher.Pusher(
    app_id='xxx',
    key='xxx',
    secret='xxxxx',
    cluster='eu',
    ssl=True
)

# set up a redis obj for caching user's cart
cart = JsonCache(str(Path(app.root_path) / 'cache' / 'cart.json'))


@app.route('/user/app')
@login_required
def user_app():

    if not current_user.confirmed:

        days = (datetime.today().date() - current_user.timeCreated.date()).days

        # if the user not confirming the account after 14 days
        if days > 14:

            full_name = current_user.contact_person

            msg = '''To fully use our services, please confirm your account in your inbox. 
            If confirmation link is no longer valid, you can request to send from here again.'''

            return render_template("account_confirmation.html",
                                   full_name=full_name,
                                   msg=msg)

    return render_template("users/index.html")


@app.route('/user/register', methods=["GET", "POST"])
def register():

    form = UserSignUpForm()

    msg_type = None

    if request.method == "POST" or form.validate_on_submit():

        full_name = form.full_name.data
        company_name = form.company_name.data

        # trim the white spaces and lower all the letters
        email = form.email.data.strip().lower()

        user = User.query.filter_by(email=email).first()

        # if this user exists
        if user:

            flash("Email already exists, please log in!", category="danger")

            return redirect(url_for('register'))

        '''checking whether if there's an existing 
        tenant with the email domain provided'''

        # Get the company domain from the email input
        domain_name = email.split("@")[1]

        # Split the domain_name into its subdomains
        subdomains = domain_name.split(".")

        main_domain = ''

        # If it's a subdomain (i.e., it has more than two parts)
        if len(subdomains) > 2:
            # Combine the last two parts to get the main domain
            main_domain = ".".join(subdomains[-2:])
        else:
            main_domain = domain_name

        # Query the Tenant table to check if a tenant with this domain or main domain exists
        existing_tenant = Tenant.query.filter(
            (Tenant.domain == domain_name) | (Tenant.domain == main_domain)).first()

        # If a tenant with this domain already exists, flash a message and redirect
        if existing_tenant:
            # Get the admin user for the tenant
            admin_user = User.query.filter_by(tenant_id=existing_tenant.id, is_admin=True).first()

            if admin_user:
                flash(
                    f"Your company {existing_tenant.company_name} is already registered, "
                    f"please contact the admin user {admin_user.email} "
                    f"to apply for an account", category="error")
            else:
                flash("Your company is already registered, but we were "
                      "unable to find the admin user. Please contact support at ops@exhausted.one", category="error")

            # redirects to sign in route
            return redirect(url_for('sign_in'))

        country = form.country.data

        password = form.password.data

        # Init a Tenant instance who is the company using the software
        new_tenant = Tenant()
        new_tenant.company_name = company_name
        new_tenant.contact_person = full_name
        # get the user's email input and assign a domain to the Tenant
        new_tenant.assign_domain_from_email(email=email)

        # create a new company in the database
        db.session.add(new_tenant)
        db.session.commit()

        # init a new User instance
        new_user = User()

        new_user.email = email
        new_user.country = country
        new_user.user_name = full_name
        new_user.company_name = company_name
        new_user.is_admin = True
        new_user.tenant_id = new_tenant.id
        new_user.role = Role(name="admin")

        # set the password for user account
        new_user.set_password(password=password)

        db.session.add(new_user)

        db.session.commit()

        welcome_msg = "Many thanks for signing up!" \
                      "Please click the following button to confirm your account. " \
                      "Token expires in 48 hours. So hurry up. "

        web_msg = "Many thanks for signing up!" \
                  "Please confirm your account within 48 hours in your email inbox. " \
                  "If the link is invalid, you can request a new link. "

        token = new_user.generate_confirmation_token()

        email_context = dict(full_name=new_user.user_name,
                             msg=welcome_msg,
                             token=token)

        html = render_template("emails/account_confirmation.html", **email_context)

        # Send user confirmation email
        try:

            user_confirmation_email(html=html,
                                    subject=f"Hi {full_name}, Welcome on board! Please confirm your account",
                                    recipients=[new_user.email])

        except Exception as e:

            print(str(e))

        # send web message
        send_web_msg(from_="system",
                     to=new_user.email,
                     text=web_msg,
                     kind="system")

        flash("Thanks for signing up. You can now log in. "
              "Meanwhile, a confirmation email has been sent to your inbox. "
              "To fully use our services, please confirm your account within 48 hours.")

        msg_type = "success"

        return redirect(url_for('sign_in'))

    context = dict(form=form,
                   msg_type=msg_type)

    return render_template("users/signup.html", **context)


# add a supplier or a partner
@app.route('/users/add/account/<string:role>', methods=["POST", "GET"])
@login_required
def add_account(role):


    '''
    :param role: supplier or partner
    :return:
    '''

    form = AddAccountForm()

    context = dict(title=f"Add new {role}",
                   form=form,
                   role=role)

    if form.validate_on_submit() or request.method == "POST":

        company_name = form.name.data
        email = form.email.data
        office_phone = form.phone.data
        address = form.street_n_no.data
        city = form.city.data
        state = form.state_or_province.data
        zip_code = form.zip_code.data
        country = form.country.data

        tax_id = form.vat_id.data
        tax_rate_1 = form.tax_rate_1.data
        tax_rate_2 = form.tax_rate_2.data

        # This acc will be created and added as a supplier
        if role == "supplier":

            # create a new supplier
            new_supplier = Supplier()

            # Assign this supplier to the user's company
            new_supplier.tenant = Tenant.query.get(current_user.tenant_id)

            new_supplier.name = company_name
            new_supplier.email = email
            new_supplier.street_n_no = address
            new_supplier.phone = office_phone
            new_supplier.zip_code = zip_code
            new_supplier.city = city
            new_supplier.state_or_province = state
            new_supplier.country = country
            new_supplier.tax_rate_1 = tax_rate_1
            new_supplier.tax_rate_2 = tax_rate_2
            new_supplier.vat_id = tax_id

            # get the warehouse opening hours from the form
            new_supplier.warehouse_start_hours = form.warehouse_start_hours.data
            new_supplier.warehouse_end_hours = form.warehouse_end_hours.data
            new_supplier.contact_person = form.contact_person.data

            db.session.add(new_supplier)

            new_supplier.set_warehouse_address()

            if not form.same_as_company_address:

                # take a different address as WH address to update if not the same as the former
                new_supplier.warehouse_address = form.warehouse_address.data

            db.session.commit()

        # Otherwise, add this account as a partner. Code to add partner goes here......
        flash(f"new {role} {company_name} has been added!", category="success")

        return redirect(url_for('suppliers'))

    return render_template("users/add_account.html", **context)


@app.route('/users/edit/account/<string:role>/<string:uuid>', methods=["POST", "GET"])
@login_required
def edit_account(role, uuid):

    account = None
    if role == "supplier":
        account = Supplier.query.filter_by(uuid=uuid, tenant_id=current_user.tenant_id).first()
    else:
        print("Partner updates")  # Replace with your Partner model query

    form = AddAccountForm(obj=account)

    context = dict(title=f"Edit {role}",
                   form=form,
                   role=role)

    if form.validate_on_submit() or request.method == "POST":
        account.name = form.name.data
        account.email = form.email.data
        account.street_n_no = form.street_n_no.data
        account.phone = form.phone.data
        account.zip_code = form.zip_code.data
        account.city = form.city.data
        account.state_or_province = form.state_or_province.data
        account.country = form.country.data
        account.tax_rate_1 = form.tax_rate_1.data
        account.tax_rate_2 = form.tax_rate_2.data
        account.vat_id = form.vat_id.data

        # Supplier specific attributes
        if role == "supplier":
            account.warehouse_start_hours = form.warehouse_start_hours.data
            account.warehouse_end_hours = form.warehouse_end_hours.data
            account.contact_person = form.contact_person.data
            account.set_warehouse_address()
            if not form.same_as_company_address.data:
                account.warehouse_address = form.warehouse_address.data

        db.session.commit()
        flash(f"{role} {form.name.data} has been updated!", category="success")
        return redirect(url_for('suppliers'))  # Or appropriate redirect for Partner

    return render_template("users/edit_account.html", **context)















