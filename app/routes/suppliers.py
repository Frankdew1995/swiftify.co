
from app import (app, render_template,
                 url_for, redirect,
                 request, make_response,
                 send_file, jsonify,
                 flash, session, mongo)

from flask_login import (login_required, login_manager,
                         login_user, logout_user,
                         current_user)

from flask_babel import format_datetime, format_date, format_decimal

from sqlalchemy import desc

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from werkzeug.utils import secure_filename

from app import db, mongo

from app.models import (User, Inventory, Quote,
                        Request, Supplier, Tenant,
                        PO)


from app.forms import (SubscribeForm, VendorSignUpForm,
                       SignInForm, AddProductForm)

from app.utils import (subscribe_user, query_products,
                       vendor_signup_email_alert, request_vendor_email_alert,
                       quote_update_email_alert, quote_received_email_alert,
                       user_confirmation_email, send_web_msg)

import json

from pathlib import Path

import csv
from uuid import uuid4
from datetime import datetime, timedelta

# Some useful variables
date_format = "%Y-%m-%d"

datetime_format = "%Y.%m.%d %H:%M:%S"


@app.route('/users/view/suppliers')
@login_required
def suppliers():

    # Retrieve current tenant's suppliers
    tenant_suppliers = Supplier.query.filter_by(tenant_id=current_user.tenant_id).all()

    context = dict(suppliers=tenant_suppliers, title="Suppliers")

    return render_template("users/view_suppliers.html", **context)


# view a supplier by uuid
@app.route('/users/view/supplier/<string:supplier_uuid>')
@login_required
def view_supplier(supplier_uuid):

    # Query the Supplier object by uuid and tenant_id
    supplier = Supplier.query.filter_by(uuid=supplier_uuid, tenant_id=current_user.tenant_id).first()

    # If supplier is None (not found or not belong to this tenant), return a 404 error
    if supplier is None:
        return "No such supplier found.", 404

    inventories = supplier.inventories.all()
    return render_template('users/view_supplier.html', supplier=supplier, inventories=inventories)


@app.route('/supplier/app')
def supplier_app():

    return render_template("suppliers/base.html")


@app.route('/vendor/app/view/pos')
def supplier_view_pos():

    return render_template("suppliers/view_pos.html")


@app.route('/supplier/view/po/<string:po_uuid>/<string:supplier_token>', methods=['GET'])
def supplier_view_po(po_uuid, supplier_token):
    po = PO.query.filter_by(uuid=po_uuid).first()

    if po is None:
        flash('Invalid PO', 'error')
        return redirect(url_for('supplier_view_pos'))

    supplier = Supplier.verify_supplier_by_token(supplier_token)

    if supplier is None or po.supplier_id != supplier.id:
        flash('Invalid or unauthorized access', 'error')
        return redirect(url_for('supplier_view_pos'))

    # Deserialize the items from JSON to Python list
    items = json.loads(po.items)

    return render_template('suppliers/view_po.html', po=po, supplier=supplier, items=items)


@app.route('/supplier/approve/po/<string:supplier_token>/<string:po_uuid>', methods=['POST', 'GET'])
def supplier_approve_po(supplier_token, po_uuid):
    # Retrieve the PO object based on the UUID
    po = PO.query.filter_by(uuid=po_uuid).first()
    if po is None:
        flash('Invalid PO', 'error')
        return redirect(url_for('supplier_view_pos'))

    supplier = Supplier.verify_supplier_by_token(supplier_token)
    if supplier is None:
        flash('Token has expired. Please contact the PO sender', 'error')
        return redirect(url_for('supplier_view_pos'))

    if request.method == 'POST':
        # Access the supplier form submission data
        quantity_list = request.form.getlist('quantity[]')
        purchase_price_list = request.form.getlist('purchase_price[]')
        tax_rate_list = request.form.getlist('tax_rate[]')

        # Update the items quantity submitted by the supplier
        items = json.loads(po.items)
        for i, item_data in enumerate(items):
            item_data['quantity'] = int(quantity_list[i])
            item_data['purchase_price'] = float(purchase_price_list[i])
            item_data['tax_rate'] = float(tax_rate_list[i])

        po.items = json.dumps(items)
        db.session.commit()

        flash('PO approved successfully', 'success')
        return redirect(url_for('supplier_view_pos'))

    return render_template('supplier_view_po.html', po=po)


@app.route('/supplier/export/po/<string:supplier_token><string:po_uuid>', methods=['GET'])
@login_required
def supplier_export_po_csv(supplier_token, po_uuid):
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

































@app.route("/vendors/view/requests/received", methods=["POST", "GET"])
@login_required
def vendor_view_requests_received():

    # validate the user for the routing
    if current_user.role != "vendor":

        return redirect(url_for('user_app'))

    # select the untouched requests by this vendor
    reqs = Request.query.filter(
        Request.owner == current_user.email,
        Request.isPending == False,
        Request.isDone == False,
    ).all()

    # Construct a req_ids 2 items key_value data store and join items as a single string
    reqs2items = {req.id: ", ".join([i.get('itemName', "") for i in json.loads(req.items)]) for req in reqs}

    context = dict(reqs=reqs,
                   reqs2items=reqs2items)

    return render_template("vendors/received_requests.html", **context)


@app.route("/vendors/view/products", methods=["POST", "GET"])
@login_required
def vendor_view_products():

    if current_user.role == "user":

        return redirect(url_for('user_app'))

    products = Product.query.all()

    products = [product for product in products
                if current_user.email in json.loads(product.vendor)]

    context = dict(products=products)

    return render_template("vendors/view_products.html", **context)


@app.route("/vendor/view/request/<int:req_id>",
           methods=["POST", "GET"])
@login_required
def vendor_view_request(req_id):

    referrer = request.headers.get('Referer')

    if current_user.role != "vendor":

        return redirect(url_for('user_app'))

    req = db.session.query(Request).get(int(req_id))

    items = json.loads(req.items)

    # populating additional information to the request for the vendor reference
    for item in items:

        item["itemName"] = Product.query.get(item['itemId']).name
        item["Brand"] = Product.query.get(item['itemId']).brand
        item["EAN / GTIN"] = Product.query.get(item['itemId']).gtin

    req.items = json.dumps(items)

    db.session.commit()

    requested_items = json.loads(req.items)

    context = dict(requested_items=requested_items,
                   req_id=req_id,
                   referrer=referrer)

    return render_template("vendors/view_request.html", **context)


# vendor works on this request and quotes the quote
@app.route('/vendor/request/update', methods=["POST"])
@login_required
def update_request():

    # if not vendor, rejects the Ajax call from the user.
    if current_user.role != "vendor":

        return {"error": "Access denied. Not a vendor"}

    quote = None

    data = request.json

    action = data.get('action')

    req_id = data.get('reqId')

    # the origin request associated with this quote
    req = db.session.query(Request).get(int(req_id))

    vendor = data.get('vendor')

    '''
    check if there's an existing quote that corresponds 
    to the same vendor and the same request
    '''

    existing_quote = db.session.query(Quote).filter(
        Quote.req_id == req_id,
        Quote.vendor == vendor).first()

    if existing_quote:

        # if so, set the existing quote to quote and only updates it
        quote = existing_quote

    else:

        # otherwise, creates a new quote object
        quote = Quote()

    quote.req_id = req_id

    quote.items = json.dumps(data.get('details'))

    quote.buyer = Request.query.get(req_id).requester

    quote.vendor = data.get('vendor')

    quote.lead_time = data.get('leadTime')

    quote.lastEdited = datetime.today()

    valid_until = None

    # if no vendor-specified date, then set today + 30days as expiry
    if data.get('validUntil') == "" or None:

        valid_until = datetime.today() + timedelta(days=30)

    else:

        valid_until = datetime.strptime(data.get('validUntil'), date_format)

    quote.valid_until = valid_until

    # Init a msg to send
    msg = None

    base_msg = f"Updates available for your quote {quote.id}. " \
               "Please view the updates in the dashboard. "

    if action.strip() == "send":

        msg = base_msg + "This quote is now complete. "

        # set the quote status as being ready
        quote.isReady = True

        # vendor sends this quote and finalized so this req is done
        req.isDone = True

    else:

        # vendor saves this quote but not finalized so this req is pending
        req.isPending = True

        msg = base_msg + "However, this quote is still being worked on and in draft mode." \
              "That means the vendor might still provide updates on this and modify the quote."

    '''if no existing quote, so we shall add new instance 
    to the session for further commit'''

    if not existing_quote:

        db.session.add(quote)

    # commit all the quote and req changes to the db
    db.session.commit()

    # Send the user quote update email
    html = render_template("emails/view_quote.html",
                           full_name=quote.buyer,
                           quote_id=quote.id,
                           msg=msg)

    quote_update_email_alert(html=html,
                             recipients=[quote.buyer],
                             subject=f"Updates available for your quote {quote.id} from vendor")

    # send the user web message
    send_web_msg(from_=quote.vendor,
                 to=quote.buyer,
                 text=msg,
                 kind="system")

    return {"success": f"quote created: {quote.id}",
            "quoteId": quote.id}


@app.route('/vendor/view/quotes/drafted')
@login_required
def vendor_drafted_quotes():

    referrer = request.headers.get('Referer')

    if current_user.role != "vendor":

        return redirect(url_for('user_app'))

    quotes = Quote.query.filter(
        Quote.vendor == current_user.email,
        Quote.isReady == False).all()

    context = dict(quotes=quotes,
                   status="pending",
                   status_class="warning",
                   referrer=referrer)

    return render_template("vendors/drafted_quotes.html", **context)


@app.route("/vendor/view/draft/quote/<int:quote_id>")
@login_required
def vendor_view_draft_quote(quote_id):

    referrer = request.headers.get('Referer')

    quote = db.session.query(Quote).get(int(quote_id))

    items = json.loads(quote.items)

    context = dict(quote_id=quote.id,
                   req_id=quote.req_id,
                   expiry=quote.valid_until,
                   lead_time=quote.lead_time,
                   items=items,
                   referrer=referrer)

    return render_template("vendors/view_drafted_quote.html", **context)


@app.route('/vendor/view/quotes/complete')
@login_required
def vendor_complete_quotes():

    referrer = request.headers.get('Referer')

    if current_user.role != "vendor":

        return redirect(url_for('user_app'))

    quotes = Quote.query.filter(
        Quote.vendor == current_user.email,
        Quote.isReady == True,
        Quote.isDeclined == False).all()

    context = dict(quotes=quotes,
                   status="sent",
                   status_class="success",
                   referrer=referrer)

    return render_template("vendors/complete_quotes.html", **context)


@app.route("/vendor/view/quote/<int:quote_id>")
@login_required
def vendor_view_quote(quote_id):

    referrer = request.headers.get('Referer')

    quote = db.session.query(Quote).get(int(quote_id))

    items = json.loads(quote.items)

    context = dict(quote_id=quote.id,
                   req_id=quote.req_id,
                   expiry=quote.valid_until,
                   lead_time=quote.lead_time,
                   items=items,
                   referrer=referrer)

    return render_template("vendors/view_quote.html", **context)


# vendor works on this request and quotes the quote
@app.route('/vendor/quote/update', methods=["POST"])
@login_required
def update_quote():

    # if not vendor, rejects the Ajax call from the user.
    if current_user.role != "vendor":

        return {"error": "Access denied. Not a vendor"}

    data = request.json

    action = data.get('action')

    quote_id = data.get('quoteId')

    req_id = data.get('reqId')

    # the origin request associated with this quote
    req = db.session.query(Request).get(int(req_id))

    vendor = data.get('vendor')

    quote = db.session.query(Quote).get(int(quote_id))

    # the current vendor is not authorized to quote here
    if quote.vendor != vendor:

        return {"error": "Access denied. Not a vendor"}

    quote.items = json.dumps(data.get('details'))

    quote.lead_time = data.get('leadTime')

    quote.lastEdited = datetime.today()

    valid_until = None

    # if no vendor-specified date, then set today + 30days as expiry
    if data.get('validUntil') == "" or None:

        valid_until = datetime.today() + timedelta(days=30)

    else:

        valid_until = datetime.strptime(data.get('validUntil'), date_format)

    quote.valid_until = valid_until

    # Init a msg to send
    msg = None

    base_msg = f"Updates available for your quote {quote.id}. " \
               "Please view the updates in the dashboard. "

    if action.strip() == "send":

        msg = base_msg + "This quote is now complete. "

        # set the quote status as being ready
        quote.isReady = True

        # vendor sends this quote and finalized so this req is done
        req.isDone = True

    else:

        # vendor saves this quote but not finalized so this req is pending
        req.isPending = True

        msg = base_msg + "However, this quote is still being worked on and in draft mode." \
              "That means the vendor will still provide updates on this and modify the quote."

    # commit all the quote and req changes to the db
    db.session.commit()

    # Send the user quote update email
    html = render_template("emails/view_quote.html",
                           full_name=quote.buyer,
                           quote_id=quote.id,
                           msg=msg)

    quote_update_email_alert(html=html,
                             recipients=[quote.buyer],
                             subject=f"Updates available for your quote {quote.id} from vendor")

    # send web message
    send_web_msg(from_=quote.vendor,
                 to=quote.buyer,
                 text=msg,
                 kind="system")

    return {"success": f"quote updated: {quote.id}",
            "quoteId": quote.id}


# vendor view rejected quotes
@app.route('/vendor/view/quotes/rejected')
@login_required
def view_rejected_quotes():

    referrer = request.headers.get('Referer')

    if current_user.role != "vendor":

        return redirect(url_for('user_app'))

    quotes = Quote.query.filter(
        Quote.vendor == current_user.email,
        Quote.isDeclined == True).all()

    context = dict(quotes=quotes,
                   status="rejected",
                   status_class="danger",
                   referrer=referrer)

    return render_template("vendors/rejected_quotes.html", **context)



