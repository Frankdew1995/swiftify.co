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


# add a warehouse / location
@app.route("/users/add/new/warehouse", methods=["POST", "GET"])
@login_required
def add_warehouse():

    # Check the current tenant_id. If none, assign the current
    if not session.get("current_tenant_id"):

        session["current_tenant_id"] = current_user.tenant_id

    form = AddWarehouseForm()

    if form.validate_on_submit():

        warehouse = Warehouse(
            warehouse_name=form.name.data,
            warehouse_manager=form.warehouse_manager.data,
            email=form.email.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zipcode=form.zip_code.data,
            country=form.country.data,
            operating_hours=f"{form.warehouse_start_hours.data.strftime('%H:%M')} - {form.warehouse_end_hours.data.strftime('%H:%M')}",
            notes=form.notes.data,
            tenant_id=session['current_tenant_id']
        )
        db.session.add(warehouse)
        db.session.commit()

        msg = f"{warehouse.warehouse_name} has been added"

        flash(msg)

        return redirect(url_for("view_warehouses"))

    context = dict(form=form,
                   title="Add a new warehouse")

    return render_template("users/add_warehouse.html", **context)


@app.route("/users/view/warehouse/<int:warehouse_id>", methods=["GET"])
@login_required
def view_warehouse(warehouse_id):
    # Fetch the warehouse with the given id from the database
    warehouse = Warehouse.query.get_or_404(warehouse_id)

    # Check if the current user has access to this warehouse. Replace this with your actual check
    if warehouse.tenant_id != current_user.tenant_id:

        flash("You do not have permission to view this warehouse.")
        return redirect(url_for('view_warehouses'))

    # Prepare the data to pass to the template
    context = {
        'warehouse': warehouse,
        'title': f"View Warehouse {warehouse.warehouse_name}"
    }

    # Render the view_warehouse.html template, passing in the warehouse data
    return render_template("users/view_warehouse.html", **context)


# users view warehouses and zones
@app.route("/users/view/warehouses", methods=["POST", "GET"])
@login_required
def view_warehouses():

    # retrieve current tenant's warehouses
    warehouses = Warehouse.query.filter_by(tenant_id=current_user.tenant_id).all()

    if warehouses:

        warehouses_list = [{
            'id': warehouse.id,
            'email': warehouse.email,
            'warehouse_name': warehouse.warehouse_name,
            'warehouse_manager': warehouse.warehouse_manager,
            'email_domain': warehouse.email_domain,
            'address': warehouse.address,
            'city': warehouse.city,
            'state': warehouse.state,
            'zipcode': warehouse.zipcode,
            'country': warehouse.country,
            'timeCreated': warehouse.timeCreated,
            'operating_hours': warehouse.operating_hours,
            'notes': warehouse.notes
        } for warehouse in warehouses]

        context = dict(warehouses=warehouses_list)

        return render_template("users/view_warehouses.html", **context)

    return render_template("users/view_warehouses.html", warehouses=warehouses)


@app.route("/users/edit/warehouse/<int:warehouse_id>", methods=["POST", "GET"])
@login_required
def edit_warehouse(warehouse_id):

    warehouse = Warehouse.query.get(warehouse_id)
    if warehouse is None or warehouse.tenant_id != current_user.tenant_id:

        flash("You do not have permission to edit this warehouse or it doesn't exist.")
        return redirect(url_for('view_warehouses'))

    form = AddWarehouseForm(obj=warehouse)

    if form.validate_on_submit():
        warehouse.warehouse_name = form.warehouse_name.data
        warehouse.warehouse_manager = form.warehouse_manager.data
        warehouse.email = form.email.data
        warehouse.address = form.address.data
        warehouse.city = form.city.data
        warehouse.state = form.state.data
        warehouse.zipcode = form.zipcode.data
        warehouse.country = form.country.data
        warehouse.operating_hours = form.operating_hours.data
        warehouse.notes = form.notes.data

        db.session.commit()

        msg = f"{warehouse.warehouse_name} has been updated"

        flash(msg)

        return redirect(url_for("view_warehouse", warehouse_id=warehouse.id))

    context = dict(form=form,
                   title="Edit Warehouse")

    return render_template("users/edit_warehouse.html", **context)


@app.route("/users/delete/warehouse/<int:warehouse_id>", methods=["GET", "POST"])
@login_required
def delete_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    if warehouse.tenant_id != current_user.tenant_id:

        flash("You do not have permission to delete this warehouse")
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))

    db.session.delete(warehouse)
    db.session.commit()
    flash("Warehouse has been deleted!", "success")
    return redirect(url_for("view_warehouses"))


@app.route("/users/view/inventories/<int:warehouse_id>", methods=["GET"])
@login_required
def view_warehouse_inventories(warehouse_id):
    # Code to get and display inventories for the warehouse with warehouse_id
    pass


@app.route("/users/manage/zones/<int:warehouse_id>", methods=["GET"])
@login_required
def manage_warehouse_zones(warehouse_id):
    # Code to manage zones for the warehouse with warehouse_id

    return redirect(url_for('view_warehouses'))
