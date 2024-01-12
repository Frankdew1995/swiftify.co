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


'''
The @admin_required is a custom decorator function that checks if the logged-in user is an admin. 
If the user isn't an admin, they are redirected to a different page or shown an error. 
This is a common pattern in web development to control access to certain routes based on the user's role or permissions.
'''


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Here, 'is_admin' is a hypothetical property or
        # method of the User model that returns True if the user is an admin
        if not current_user.is_admin:
            flash('You do not have permission to view this page.', 'warning')
            # redirect to some general page
            return redirect(url_for('user_app'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/users/account/user/add', methods=['GET', 'POST'])
@login_required
def add_user():

    # Ensure that the current user is admin
    if not current_user.is_admin:
        abort(403)
        flash('You cannot add users as a non-admin user', 'danger')
        return redirect(url_for('company_settings'))

    organization = current_user.tenant.company_name

    form = UserForm()
    # prevent super user for application owner from being created
    form.role_id.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all() if role.name!="super"]
    form.tenant_id.data = current_user.tenant_id

    if form.validate_on_submit():

        # Trim spaces and convert to lowercase
        email = form.email.data.strip().lower()

        # Check if the user already exists
        user = User.query.filter_by(email=email,
                                    tenant_id=current_user.tenant_id).first()

        if user:
            flash('User already exists!', category='error')
            return redirect(url_for('company_settings'))

        # Create a new user instance
        new_user = User(
            user_name=form.user_name.data,
            email=email,
            role_id=form.role_id.data,
            tenant_id=form.tenant_id.data)

        new_user.set_password(password=form.password.data)

        # Add the user to the session
        db.session.add(new_user)
        # Commit the transaction
        db.session.commit()

        # sending an email to the user for the verification
        welcome_msg = "Cool you're here!" \
                      f"You're invited to join {organization} on Exhausted.one, " \
                      f"a modern supply chain management platform made by frankdu.co. " \
                      "Token expires in 48 hours. So hurry up and join now"

        token = new_user.generate_confirmation_token()

        email_context = dict(full_name=new_user.user_name,
                             msg=welcome_msg,
                             token=token)

        html = render_template("emails/add_user_confirmation.html", **email_context)

        # Send user confirmation email
        try:

            user_confirmation_email(html=html,
                                    subject=f"Hi {new_user.user_name}, Welcome on board! Please confirm to join {organization}",
                                    recipients=[new_user.email])

        except Exception as e:

            print(str(e))

        flash(f'New user {new_user.user_name} has been created.', 'success')
        return redirect(url_for('company_settings'))

    context = dict()
    context['form'] = form
    context['title'] = f'Add a user for {current_user.tenant.company_name} '

    return render_template('users/add_user.html', **context)


@app.route('/users/account/user/activate/<int:tenant_id>/<int:user_id>', methods=['GET'])
@login_required
def activate_user(tenant_id, user_id):

    # Ensure that the current user is admin
    if not current_user.role.name == 'admin':
        flash('You cannot modify users as a non-admin user', 'error')
        return redirect(url_for('company_settings'))

    # Ensure that the current user belongs to the right tenant
    if not current_user.tenant_id == tenant_id:
        flash('You cannot modify users from a different tenant', 'danger')
        return redirect(url_for('company_settings'))

    # Fetch the user to be activated
    user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('company_settings'))

    # Activate the user
    user.activated = True
    db.session.commit()

    flash(f'User {user.user_name} {user.email} has been activated.', 'success')
    return redirect(url_for('company_settings'))


@app.route('/users/account/user/deactivate/<int:tenant_id>/<int:user_id>', methods=['GET'])
@login_required
def deactivate_user(tenant_id, user_id):

    # Ensure that the current user is admin
    if not current_user.role.name == 'admin':
        flash('You cannot modify users as a non-admin user', 'danger')
        return redirect(url_for('company_settings'))

    # Ensure that the current user belongs to the right tenant
    if not current_user.tenant_id == tenant_id:
        flash('You cannot modify users from a different tenant', 'danger')
        return redirect(url_for('company_settings'))

    # Fetch the user to be deactivated
    user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('company_settings'))

    # Deactivate the user
    user.activated = False
    db.session.commit()

    flash(f'User {user.user_name} {user.email} has been deactivated.', 'success')
    return redirect(url_for('company_settings'))


@app.route("/user/<int:tenant_id>/<int:user_id>/view", methods=['GET'])
@login_required
@admin_required
def view_user(tenant_id, user_id):
    # Query for the user based on the tenant_id and user_id
    user = User.query.filter_by(tenant_id=tenant_id, id=user_id).first()

    # If no user is found, return an error message
    if not user:
        flash('No user found', 'error')
        return redirect(url_for('company_settings'))

    return render_template('users/view_user.html', user=user)


@app.route("/user/<int:tenant_id>/<int:user_id>/edit", methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(tenant_id, user_id):
    # Query for the user based on the tenant_id and user_id
    user = User.query.filter_by(tenant_id=tenant_id, id=user_id).first()
    # un_modified_name
    user_name = user.user_name

    # If no user is found, return an error message
    if not user:
        flash('No user found', 'error')
        return redirect(url_for('company_settings'))

    # Create a form instance with the data of the user
    form = UserForm()

    # If the form validates on submission
    if form.validate_on_submit() or request.method == "POST":
        # Update the user's attributes
        user.user_name = form.user_name.data
        user.email = form.email.data
        user.role_id = int(form.role_id.data)

        db.session.commit()

        flash(f'User {user_name} has been updated.', 'success')

        return redirect(url_for('view_user', tenant_id=tenant_id, user_id=user_id))

    else:
        form = UserForm(obj=user)
        form.role_id.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all() if
                                role.name != "super"]

    return render_template('users/edit_user.html', form=form, user=user)

