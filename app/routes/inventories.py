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


# add an inventory item
@app.route("/users/add/new/product", methods=["POST", "GET"])
@login_required
def add_product():

    # inherit the attributes from add product form
    class FormWithVendor(AddProductForm):

        tenant_suppliers = Supplier.query.filter_by(tenant_id=current_user.tenant_id).all()

        tenant_warehouses = Warehouse.query.filter_by(tenant_id=current_user.tenant_id).all()

        # list of tuples for choices in multi select form
        suppliers = [(vendor.id, vendor.name) for vendor in tenant_suppliers]

        warehouses = [(warehouse.warehouse_name, warehouse.warehouse_name) for warehouse in tenant_warehouses]

        # init new attributes
        suppliers = SelectMultipleField("Suppliers", choices=suppliers)

        # Init new warehouse and zones features
        warehouses = SelectField("Receiving Warehouse", choices=warehouses)

    form = FormWithVendor()

    if form.validate_on_submit() or request.method == "POST":

        # create a new inventory item
        product = Inventory()

        product.name = form.name.data
        product.gtin = form.gtin.data
        product.colli_barcode = form.colli_barcode.data
        product.description = form.desc.data
        product.stock_quantity = form.stock_quantity.data
        product.price = form.purchase_price.data
        product.origin = form.country.data

        if form.image.data:

            file_name = secure_filename(form.image.data.filename)

            # get the file format by str parsing
            file_format = str(file_name).split('.')[1]

            image_name = str(uuid4())

            save_file_name = f'{image_name}.{file_format}'

            # Pathlib object
            save_folder = Path(app.root_path) / 'static' / 'img' / 'product_images'

            # save the product image data file from the form
            img_path = str(save_folder / save_file_name)

            form.image.data.save(img_path)

            # save product image name
            product.img = save_file_name

        # Input PU Data
        product.pu_quantity = form.pu.data
        product.pu_gw = form.pu_gw.data
        product.pu_length = form.pu_length.data
        product.pu_width = form.pu_width.data
        product.pu_height = form.pu_height.data

        # Input Palletization Data
        product.palletized_quantity = form.palletized_quantity.data
        product.palletized_gw = form.palletized_gw.data
        product.pallet_length = form.pallet_length.data
        product.pallet_width = form.pallet_width.data
        product.pallet_height = form.pallet_height.data

        # CUSTOMS DATA
        product.hs_code = form.hs_codes.data
        product.vat = form.tax_rate.data
        product.stock_location = form.warehouses.data

        # associate the product with the tenant id
        product.tenant_id = current_user.tenant_id

        # finally adding the product
        db.session.add(product)
        db.session.commit()

        supplier_ids = form.suppliers.data

        # return the suppliers that's been selected from this tenant to be assigned to a product
        assigned_suppliers = Supplier.query.filter(
            Supplier.tenant_id == current_user.tenant_id,
            Supplier.id.in_(supplier_ids)
        ).all()

        # add each supplier to be associated with this inventory item
        for supplier in assigned_suppliers:

            product.suppliers.append(supplier)

        # commit the changes in the end
        db.session.commit()
        msg = f"{product.name} has been added"

        flash(msg)

        return redirect(url_for("view_products"))

    context = dict(form=form,
                   title="Add new inventory item")

    return render_template("users/add_product.html", **context)


@app.route('/users/view/product/<string:product_uuid>')
@login_required
def view_product(product_uuid):

    # Query the product by its uuid and tenant_id
    product = Inventory.query.filter_by(uuid=product_uuid, tenant_id=current_user.tenant_id).first()

    if product is None:

        flash("No such product found.")
        return redirect(url_for("view_products"))

    context = {
        'product': product,
        'title': f"View product: {product.name}",
        'name': product.name,
        'en_name': product.en_name,
        'brand': product.brand,
        'category': product.category,
        'description': product.description,
        'price': product.price,
        'vat': product.vat,
        'gtin': product.gtin,
        'colli_barcode': product.colli_barcode,
        'item_code': product.item_code,
        'hs_code': product.hs_code,
        'origin': product.origin,
        'img': product.img if "https://" in product.img else
                url_for('static', filename=f"img/product_images/{product.img}"),
        'is_available': product.is_available,
        'time_created': product.time_created,
        'palletized_quantity': product.palletized_quantity,
        'palletized_gw': product.palletized_gw,
        'pallet_length': product.pallet_length,
        'pallet_width': product.pallet_width,
        'pallet_height': product.pallet_height,
        'pu_quantity': product.pu_quantity,
        'pu_gw': product.pu_gw,
        'pu_length': product.pu_length,
        'pu_width': product.pu_width,
        'pu_height': product.pu_height,
        'stock_quantity': product.stock_quantity,
        'stock_location': product.stock_location,
        'tenant_id': product.tenant_id,
        'suppliers': [supplier.name for supplier in product.suppliers],
        'uuid': product.uuid
    }

    return render_template("users/view_product.html", **context)


# Export product to csv
@app.route('/users/export/product/<string:product_uuid>/csv', methods=["GET", "POST"])
@login_required
def export_product_csv(product_uuid):
    # Query the product by its uuid and tenant_id
    product = Inventory.query.filter_by(uuid=product_uuid, tenant_id=current_user.tenant_id).first()

    if product is None:
        flash("No such product found.")
        return redirect(url_for("view_products"))

    product_data = {
        'title': product.name,
        'name': product.name,
        'en_name': product.en_name,
        'brand': product.brand,
        'category': product.category,
        'description': product.description,
        'price': product.price,
        'vat': product.vat,
        'barcode / ean': product.gtin,
        'colli_barcode': product.colli_barcode,
        'item_code': product.item_code,
        'hs_code': product.hs_code,
        'origin': product.origin,
        'img': product.img if "https://" in product.img else
                url_for('static', filename=f"img/product_images/{product.img}"),
        'is_available': product.is_available,
        'time_created': product.time_created,
        'palletized_quantity': product.palletized_quantity,
        'palletized_gw': product.palletized_gw,
        'pallet_length': product.pallet_length,
        'pallet_width': product.pallet_width,
        'pallet_height': product.pallet_height,
        'pu_quantity': product.pu_quantity,
        'pu_gw': product.pu_gw,
        'pu_length': product.pu_length,
        'pu_width': product.pu_width,
        'pu_height': product.pu_height,
        'stock_quantity': product.stock_quantity,
        'stock_location': product.stock_location,
        'uuid': product.uuid
    }

    # Otherwise, generate as CSV
    csv_file = f"{product.name}_{product_uuid}.csv"
    csv_path = os.path.join(os.getcwd(), csv_file)

    with open(csv_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(product_data.keys())
        writer.writerow(product_data.values())

    response = send_file(csv_path, mimetype='text/csv', attachment_filename=csv_file, as_attachment=True)

    # delete the file after sending it
    remove(csv_path)

    return response


# Route for editing or updating a product
@app.route("/users/edit/product/<string:product_uuid>", methods=["GET", "POST"])
@login_required
def edit_product(product_uuid):
    # Query the product by its uuid and tenant_id
    product = Inventory.query.filter_by(uuid=product_uuid, tenant_id=current_user.tenant_id).first()

    if product is None:
        flash("No such product found.")
        return redirect(url_for("view_products"))

    # inherit the attributes from add product form
    class FormWithVendor(AddProductForm):

        tenant_suppliers = Supplier.query.filter_by(tenant_id=current_user.tenant_id).all()

        tenant_warehouses = Warehouse.query.filter_by(tenant_id=current_user.tenant_id).all()

        # list of tuples for choices in multi select form
        suppliers = [(vendor.id, vendor.name) for vendor in tenant_suppliers]

        warehouses = [(warehouse.id, warehouse.warehouse_name) for warehouse in tenant_warehouses]

        # init new attributes
        suppliers = SelectMultipleField("Select Supplier(s)", choices=suppliers,
                                        default=[supplier.id for supplier in tenant_suppliers])

        # Init new warehouse and zones features
        warehouses = SelectField("Receiving Warehouse", choices=warehouses, default=product.stock_location)

        update = SubmitField("Update")

    # fill the form with current product's data
    form = FormWithVendor(obj=product)

    if form.validate_on_submit() or request.method == "POST":

        product.name = form.name.data
        product.gtin = form.gtin.data
        product.colli_barcode = form.colli_barcode.data
        product.description = form.desc.data
        product.stock_quantity = form.stock_quantity.data
        product.price = form.purchase_price.data
        product.origin = form.country.data

        if form.image.data:
            file_name = secure_filename(form.image.data.filename)

            # get the file format by str parsing
            file_format = str(file_name).split('.')[1]

            image_name = str(uuid4())

            save_file_name = f'{image_name}.{file_format}'

            # Pathlib object
            save_folder = Path(app.root_path) / 'static' / 'img' / 'product_images'

            # save the product image data file from the form
            img_path = str(save_folder / save_file_name)

            form.image.data.save(img_path)

            # save product image name
            product.img = save_file_name

        # Input PU Data
        product.pu_quantity = form.pu.data
        product.pu_gw = form.pu_gw.data
        product.pu_length = form.pu_length.data
        product.pu_width = form.pu_width.data
        product.pu_height = form.pu_height.data

        # Input Palletization Data
        product.palletized_quantity = form.palletized_quantity.data
        product.palletized_gw = form.palletized_gw.data
        product.pallet_length = form.pallet_length.data
        product.pallet_width = form.pallet_width.data
        product.pallet_height = form.pallet_height.data

        # CUSTOMS DATA
        product.hs_code = form.hs_codes.data
        product.vat = form.tax_rate.data
        product.stock_location = form.warehouses.data

        # associate the product with the tenant id
        product.tenant_id = current_user.tenant_id

        db.session.commit()

        # only suppliers are selected to execute this.
        if form.suppliers.data:

            supplier_ids = form.suppliers.data

            # Get the new suppliers to be associated with the product
            new_suppliers = Supplier.query.filter(
                Supplier.tenant_id == current_user.tenant_id,
                Supplier.id.in_(supplier_ids)
            ).all()

            # Get the current suppliers associated with the product
            current_suppliers = product.suppliers

            # Add new suppliers that are not already associated with the product
            for supplier in new_suppliers:
                if supplier not in current_suppliers:
                    product.suppliers.append(supplier)

            # Remove old suppliers that are not selected in the form
            for supplier in current_suppliers:
                if supplier not in new_suppliers:
                    product.suppliers.remove(supplier)

        db.session.commit()

        flash("Product details have been updated.")

        return redirect(url_for("view_products"))

    # get request and fill the form data with current product's data
    else:

        # In case of a GET request, we manually assign the data.
        form.country.data = product.origin
        form.hs_codes.data = product.hs_code
        form.tax_rate.data = product.vat
        form.purchase_price.data = product.price
        form.pu.data = product.pu_quantity

        form.warehouses.data = product.stock_location

    current_supplier_s = ", ".join([supplier.name for supplier in product.suppliers])
    context = dict(form=form,
                   selected="",
                   title=f"Edit product {product.name}",
                   current_supplier_s=current_supplier_s,
                   image=url_for('static', filename=f"img/product_images/{product.img}"))

    return render_template("users/edit_product.html", **context)


# users view products
@app.route("/users/view/products", methods=["POST", "GET"])
@login_required
def view_products():
    tenant = Tenant.query.get(current_user.tenant_id)

    inventories = tenant.inventories
    currency = get_currency_symbol(currency_code=tenant.currency)
    context = dict(products=inventories,
                   currency=currency)

    return render_template("users/view_products.html", **context)

