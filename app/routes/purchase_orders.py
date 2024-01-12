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

from app import db, mongo, documents_changelog_store

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
                       CreatePOForm, UserForm, FileUploadForm)

from app.utils import (user_confirmation_email,
                       send_quote_or_request_via_email,
                       quote_rejection_vendor_email_alert, email_invoice,
                       html2pdf, get_image_file_as_base64_data,
                       query_products, RedisCache,
                       request_vendor_email_alert, quote_update_email_alert,
                       quote_received_email_alert, send_web_msg, JsonCache,
                       return_currencies, get_currency_symbol,
                       po_messenger, import_pos_from_salesbinder)

import json

from pathlib import Path

import csv
from uuid import uuid4
from datetime import datetime
import io
import csv
import requests

import os
from os import remove
from functools import wraps
from config import Config
from io import StringIO


@app.route('/users/view/pos')
@login_required
def view_pos():

    # only retrieve current tenant's POs
    pos = PO.query.filter(PO.tenant_id == current_user.tenant_id).all()

    currency = get_currency_symbol(currency_code=current_user.tenant.currency)

    status2badge = {"Overdue": "warning",
                    "Sent": "info",
                    "Paid": "success",
                    "Draft": "primary"
                    }

    context = dict(pos=pos,
                   status2badge=status2badge,
                   currency=currency,
                   format_currency=format_currency)

    if len(pos) > 0:

        context["purchase_orders"] = pos

    return render_template("users/view_pos.html", **context)


@app.route('/users/create/po', methods=['GET', 'POST'])
@login_required
def create_po():

    form = CreatePOForm()

    # render date from server
    today = datetime.now().date().isoformat()

    # Get the current tenant's suppliers and inventory items
    suppliers = Supplier.query.filter_by(tenant_id=current_user.tenant_id).all()
    inventory_items = Inventory.query.filter_by(tenant_id=current_user.tenant_id).all()
    warehouses = Warehouse.query.filter_by(tenant_id=current_user.tenant_id).all()

    # get current tenant
    current_tenant = Tenant.query.get(current_user.tenant_id)

    currency = current_tenant.currency

    # Pass these to the form
    form.supplier.choices = [(s.uuid, s.name) for s in suppliers]
    form.items.choices = [(i.id, i.name) for i in inventory_items]
    form.warehouse.choices = [(w.id, w.warehouse_name) for w in warehouses]

    if form.validate_on_submit():
        po = PO(
            items=form.items.data,
            buyer=current_user.name,
            valid_until=form.valid_until.data,
            lead_time=form.lead_time.data,
            supplier_notes=form.supplier_notes.data,
            warehouse_notes=form.warehouse_notes.data,
            status="Pending",
            expected=form.expected.data,
            subtotal=form.subtotal.data,
            discount=form.discount.data,
            shipping_charges=form.shipping_charges.data,
            total=form.total.data,
            tenant_id=current_user.tenant_id,
            supplier_id=form.supplier.data,
            warehouse_id=form.warehouse.data
        )
        db.session.add(po)
        db.session.commit()

        flash("Purchase order created successfully.", "success")
        return redirect(url_for('view_po', po_id=po.id))

    return render_template('users/create_po.html',
                           form=form,
                           currency=currency,
                           today=today)


@app.route('/users/view/po/<string:po_uuid>', methods=['GET', "POST"])
@login_required
def view_po(po_uuid):

    # Query for the PO with the given UUID
    po = PO.query.filter_by(uuid=po_uuid).first()

    # If no such PO exists, return an error
    if po is None:
        flash('No such Purchase Order found', 'error')
        return redirect(url_for('view_pos'))

    # access the change log from Redis server
    change_logs_raw = documents_changelog_store.lrange(po_uuid, 0, -1)
    # Deserialize the logs from JSON and add an 'is_modified' key to each log
    change_logs = []
    for log in change_logs_raw:
        log = json.loads(log)
        log['is_modified'] = log['previous_items'] != log['current_items']
        previous_quantities = {item['item_name']: item['quantity'] for item in log['previous_items']}
        current_quantities = {item['item_name']: item['quantity'] for item in log['current_items']}

        change_logs.append(log)

    # Convert the items from a JSON string to a Python list
    items = json.loads(po.items)

    warehouse = po.warehouse
    supplier = po.supplier

    tenant = current_user.tenant

    # processing the source data for auto-complete
    source_data = []
    if warehouse:
        source_data.append({'label': f'Warehouse {warehouse.warehouse_name}',
                            'value': warehouse.email})

    if supplier:
        source_data.append({'label': f'Supplier {supplier.name}',
                            'value': supplier.email})

    for user in tenant.users:
        user_contact = {'label': f"User {user.user_name}", 'value': user.email}
        source_data.append(user_contact)

    activities = db.session.query(Activity).filter(Activity.po_id==po.id).order_by(desc(Activity.timestamp)).all()

    currency = get_currency_symbol(currency_code=current_user.tenant.currency)

    # Create an instance of the FileUploadForm
    form = FileUploadForm()

    # associate the file with the PO by naming the folder name as UUID
    save_folder = Path(app.root_path) / 'cache' / 'files' / po_uuid

    # Check if the folder exists
    if not save_folder.exists():
        save_folder.mkdir(parents=True)

        # Handle form submission for saving file for this PO
    if form.validate_on_submit() or request.method == "POST":
        file = form.file.data

        # Save the file to a desired location
        file.save(str(save_folder / file.filename))

        # Instantiate a activity to this action
        message = f"{current_user.user_name} uploaded a file {file.filename}"
        activity = Activity(
            text=message,
            sender_id=current_user.id,
            tenant_id=current_user.tenant_id,
            type='event',
            po_id=po.id,
            warehouse_id=po.warehouse_id if po.warehouse_id else 0)
        try:
            db.session.add(activity)
            db.session.commit()
        except Exception as e:
            # Rollback in case of error
            db.session.rollback()
            print("Failed to add activity. Error: ", str(e))

        flash('File uploaded successfully', 'success')
        return redirect(url_for('view_po', po_uuid=po_uuid))

    # Return the PO data and items to the template
    return render_template('users/view_po.html',
                           po=po,
                           items=items,
                           warehouse=warehouse,
                           tenant=tenant,
                           supplier=supplier,
                           activities=activities,
                           currency=currency,
                           form=form,
                           source_data=source_data,
                           change_logs=change_logs)


@app.route('/users/view/po/<string:po_uuid>/changelog', methods=['GET'])
@login_required
def view_po_changelog(po_uuid):
    # Query for the PO with the given UUID
    po = PO.query.filter_by(uuid=po_uuid).first()

    # If no such PO exists, return an error
    if po is None:
        flash('No such Purchase Order found', 'error')
        return redirect(url_for('view_pos'))

    # Access the change log from Redis server
    change_logs_raw = documents_changelog_store.lrange(po_uuid, 0, -1)

    # Deserialize the logs from JSON and add an 'is_modified' key to each log
    change_logs = []
    for log in change_logs_raw:
        log = json.loads(log)
        log['is_modified'] = log['previous_items'] != log['current_items']
        previous_quantities = {item['item_name']: item['quantity'] for item in log['previous_items']}
        current_quantities = {item['item_name']: item['quantity'] for item in log['current_items']}
        change_logs.append(log)

    return render_template('users/po_change_log.html',
                           change_logs=change_logs,
                           po=po)


@app.route('/users/edit/po/<string:po_uuid>', methods=['GET', 'POST'])
@login_required
def edit_po(po_uuid):

    # Query for the PO with the given UUID
    po = PO.query.filter_by(uuid=po_uuid).first()

    # If no such PO exists, return an error
    if po is None:
        flash('No such Purchase Order found', 'error')
        return redirect(url_for('view_pos'))

    # Create a form instance with the PO data
    form = CreatePOForm(obj=po)

    # Get the current tenant's suppliers and inventory items
    suppliers = Supplier.query.filter_by(tenant_id=current_user.tenant_id).all()
    inventory_items = Inventory.query.filter_by(tenant_id=current_user.tenant_id).all()
    warehouses = Warehouse.query.filter_by(tenant_id=current_user.tenant_id).all()

    # Pass data to the form conditionally
    # if this po has no supplier, lets user set one from the choices
    supplier_readonly = ''
    if not po.supplier:
        form.supplier.choices = [(s.uuid, s.name) for s in suppliers]
        no_supplier_tup = (str(uuid4()),
                           "No Supplier Warning, please config now")
        form.supplier.choices.append(no_supplier_tup)
        # set the warning message / key > value pair
        form.supplier.data = no_supplier_tup[0]

    else:
        # You cannot change supplier after a PO creation / issuance with an existing supplier
        form.supplier.choices = [(s.uuid, s.name) for s in suppliers if s.uuid == po.supplier.uuid]
        form.supplier.data = po.supplier.uuid
        supplier_readonly = "readonly"

    # checking whether this po has a receiving warehouse
    if not po.warehouse:
        form.warehouse.choices = [(w.id, w.warehouse_name) for w in warehouses]
        no_warehouse_tup = (str(0), "No Warehouse Associated, or this is a drop-shipped PO")
        form.warehouse.choices.append(no_warehouse_tup)

        # set the warehouse warning message / key > value pair
        form.warehouse.data = no_warehouse_tup[0]

    else:
        form.warehouse.choices = [(w.id, w.warehouse_name) for w in warehouses]
        form.warehouse.data = po.warehouse.id

    form.items.choices = [(i.id, i.name) for i in inventory_items]

    if form.validate_on_submit():
        # Update the PO data with the form data
        form.populate_obj(po)

        # Save the updated PO to the database
        db.session.commit()

        flash('Purchase Order updated successfully', 'success')
        return redirect(url_for('view_po', po_uuid=po_uuid))

    currency = get_currency_symbol(currency_code=current_user.tenant.currency)

    return render_template('users/edit_po.html',
                           form=form,
                           po=po,
                           items=json.loads(po.items),
                           currency=currency,
                           supplier_readonly=supplier_readonly)


@app.route('/users/sync/pos/salesbinder', methods=['GET'])
@login_required
def sync_pos():

    api_key = current_user.tenant.salesbinder_api_key
    subdomain = current_user.tenant.salesbinder_subdomain

    tenant = current_user.tenant

    pos = import_pos_from_salesbinder(
        api_key=current_user.tenant.salesbinder_api_key,
        subdomain=current_user.tenant.salesbinder_subdomain)

    converted_pos = []

    for sample_po in pos:

        mapped_items = []

        buyer = current_user.user_name
        supplier_notes = sample_po.get('public_note')
        warehouse_notes = sample_po.get('public_note')
        po_number = sample_po.get('document_number')
        total = sample_po.get('total_price', 0)
        tax_amount = sample_po.get('total_tax', 0) + sample_po.get('total_tax2', 0)
        subtotal = total - tax_amount
        issue_date = sample_po.get('issue_date')
        po_uuid = sample_po.get('id')

        # Check if a PO with this uuid already exists in the database
        existing_po = PO.query.filter_by(uuid=po_uuid).first()

        if existing_po is not None:
            # If a PO with this uuid already exists, skip it
            continue

        status = sample_po.get('status').get('name')
        supplier_name = sample_po.get('customer').get('name')

        supplier = Supplier.query.filter_by(tenant_id=tenant.id, name=supplier_name).first()

        # instantiate a new dict to hold the preliminary PO data
        converted_po = dict(
            buyer=buyer,
            supplier_notes=supplier_notes,
            warehouse_notes=warehouse_notes,
            total=total,
            subtotal=subtotal,
            time_created=issue_date,
            status=status,
            tax_amount=tax_amount,
            po_uuid=po_uuid,
            po_number=po_number)

        if supplier is None:

            account_number = sample_po.get('customer').get('customer_number')

            # create a new supplier
            new_supplier = Supplier()

            # Assign this supplier to the user's company
            new_supplier.tenant = tenant
            new_supplier.name = supplier_name
            new_supplier.account_number = account_number

            # Try to add and commit the new supplier to the database
            try:
                db.session.add(new_supplier)
                db.session.commit()

                # supplier database table instance
                converted_po['supplier'] = new_supplier

            except Exception as e:
                # Rollback in case of error
                db.session.rollback()
                print("Failed to add supplier. Error: ", str(e))
        else:
            # supplier database table instance
            converted_po['supplier'] = supplier

        po_items = sample_po.get('document_items')

        for item in po_items:

            item_id = item.get('item_id')
            item_target = f"https://{api_key}:x@{subdomain}.salesbinder.com/api/2.0/items/{item_id}.json"
            item_found = requests.get(item_target).json().get("item")

            # Write empty item
            if item_found is not None:

                barcode = item_found.get('sku')

                image = ''
                image_data = item_found.get('images')

                # if the item has images
                if len(image_data) > 0:

                    image = image_data[0].get('url_original')

                mapped_item = {
                    "image": image,
                    "item_name": item.get('item').get('name', ''),
                    "barcode": barcode,
                    "quantity": item.get('quantity', 0),
                    "purchase_price": item.get('price', 0),
                    "tax_rate": item.get('tax', 0) + item.get('tax2', 0),
                    "subtotal": item.get('quantity', 0) * item.get('price', 0),
                    'uuid': item.get('item_id')
                }

                mapped_items.append(mapped_item)
                inventory = Inventory.query.filter_by(gtin=barcode,
                                                      tenant_id=tenant.id).first()

                # if this item does not exist
                if inventory is None:
                    inventory = Inventory(tenant_id=tenant.id)
                    inventory.gtin = barcode
                    inventory.name = item.get('item').get('name', '')
                    inventory.price = item.get('price', 0)
                    inventory.suppliers.append(supplier)
                    inventory.vat = item.get('tax', 0) + item.get('tax2', 0)
                    inventory.uuid = item.get('item_id')
                    inventory.img = image

                    # Try to add and commit new inventory to the database
                    try:
                        db.session.add(inventory)
                        db.session.commit()
                    except Exception as e:
                        # Rollback in case of error
                        db.session.rollback()
                        print("Failed to add supplier. Error: ", str(e))

        converted_po['items'] = mapped_items
        converted_pos.append(converted_po)

    # Calling the function to add converted POs to the database
    add_converted_pos_to_db(converted_pos=converted_pos,
                            tenant=tenant)

    flash('all POs have been scanned and imported from SalesBidner', 'success')
    return redirect(url_for('view_pos'))


# utility function
def add_converted_pos_to_db(converted_pos, tenant):
    pos = []
    for converted_po in converted_pos:

        # be careful with why tenant_id is sometimes not being set.
        po = PO(tenant=tenant)

        # Basic fields
        po.buyer = converted_po.get('buyer')
        po.supplier_notes = converted_po.get('supplier_notes')
        po.warehouse_notes = converted_po.get('warehouse_notes')
        po.total = converted_po.get('total')
        po.subtotal = converted_po.get('subtotal')

        time_created = converted_po.get('time_created')
        # offset timezones
        try:
            po.timeCreated = datetime.strptime(time_created, '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            # Try parsing without timezone offset
            po.timeCreated = datetime.strptime(time_created, '%Y-%m-%dT%H:%M:%S')

        po.status = converted_po.get('status')
        po.tax_amount = converted_po.get('tax_amount')

        po.supplier = converted_po.get('supplier')

        po.po_number = converted_po.get('po_number')

        # Serialized items
        po.items = json.dumps(converted_po.get('items'))

        # Handle the UUID and PO number
        po.uuid = converted_po.get('po_uuid')

        pos.append(po)

    try:
        db.session.add_all(pos)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Failed to add converted POs. Error: ", str(e))


@app.route('/users/export/po/<string:po_uuid>', methods=['GET'])
@login_required
def export_po_csv(po_uuid):
    # Query for the PO with the given UUID
    po = PO.query.filter_by(uuid=po_uuid).first()

    # If no such PO exists, return an error
    if po is None:
        flash('No such Purchase Order found', 'error')
        return redirect(url_for('view_pos'))

    tenant_name = po.tenant.company_name

    # Retrieve the PO items
    items = json.loads(po.items)

    # Create a file-like object in memory
    csv_data = StringIO()

    # Create a CSV writer
    writer = csv.writer(csv_data)

    # Write the header row
    writer.writerow(['Item Name', 'Barcode', 'Quantity', 'Purchase Price', 'Tax Rate', 'Subtotal'])

    # Write each item as a row in the CSV file
    for item in items:
        item_name = item.get('item_name', '')
        barcode = item.get('barcode', '')
        quantity = item.get('quantity', '')
        purchase_price = item.get('purchase_price', '')
        tax_rate = item.get('tax_rate', '')
        subtotal = item.get('subtotal', '')

        writer.writerow([item_name, barcode, quantity, purchase_price, tax_rate, subtotal])

    # associate the file with the PO by naming the folder name as UUID
    save_folder = Path(app.root_path) / 'cache' / 'files' / po_uuid

    # Check if the folder exists
    if not save_folder.exists():
        save_folder.mkdir(parents=True)

    # Set the CSV file name
    filename = f'po_{po_uuid}_{tenant_name}.csv'

    file_path = str(save_folder / filename)

    # Save the CSV file
    with open(file_path, 'w', newline='') as file:
        file.write(csv_data.getvalue())

    # Create a CSV response
    response = make_response(csv_data.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/csv'

    return response

