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

import json
from uuid import uuid4
import csv
from pathlib import Path
from app.utils import send_web_msg


@app.route('/user/quotes/view/drafted')
@login_required
def view_drafted_quotes():

    if current_user.role != "user":

        return redirect(url_for('vendor_app'))

    quotes = Quote.query.filter(Quote.buyer == current_user.email,
                                Quote.isReady == False,
                                Quote.isExpired == False,
                                Quote.isDeclined == False).all()

    # Construct a quotes 2 items key_value data store and join items as a single string
    quotes2items = {quote.id: ", ".join([i.get('itemName', "")
                    for i in json.loads(quote.items)]) for quote in quotes}

    context = dict(status="Open",
                   status_class="warning",
                   quotes=quotes,
                   quotes2items=quotes2items,
                   title="Drafted quotes",
                   format_datetime=format_datetime)

    return render_template("users/drafted_quotes.html", **context)


@app.route('/user/quotes/view/ready')
@login_required
def view_ready_quotes():

    if current_user.role != "user":

        return redirect(url_for('vendor_app'))

    quotes = Quote.query.filter(Quote.buyer == current_user.email,
                                Quote.isReady == True,
                                Quote.isDeclined == False,
                                Quote.isExpired == False).all()

    # Construct a quotes 2 items key_value data store and join items as a single string
    quotes2items = {quote.id: ", ".join([i.get('itemName', "")
                    for i in json.loads(quote.items)]) for quote in quotes}

    context = dict(status="Ready",
                   status_class="success",
                   quotes=quotes,
                   quotes2items=quotes2items,
                   title="Complete quotes",
                   format_datetime=format_datetime)

    return render_template("users/complete_quotes.html", **context)


@app.route('/user/quote/view/<int:quote_id>', methods=["GET", "POST"])
@login_required
def view_quote(quote_id):

    send_email_form = SendEmailForm()

    reject_form = RejectQuoteForm()

    # always valid the role of a user for routing.
    if current_user.role != "user":

        return redirect(url_for('vendor_app'))

    referrer = request.headers.get('Referer')

    quote = Quote.query.get(int(quote_id))

    items = json.loads(quote.items)

    lead_time = quote.lead_time

    expiry = quote.valid_until

    # if the user types in the email and hit the send button
    if send_email_form.validate_on_submit():

        recipient = send_email_form.email.data

        file_name = f"quote_id_{quote_id}_" + str(uuid4()) + ".csv"

        file = str(Path(app.root_path) / 'cache' / 'user_exports' / file_name)

        headers = ("Item ID", "Name", "Brand",
                   "Barcode / GTIN / EAN", "Requested Quantity", "Unit",
                   "vendor price exw €", "Deliverable Quantity", "Lead time - working days",
                   "valid until", "amazon url", "item code",
                   "hs code")

        with open(file, mode="w", encoding="utf8") as f:

            writer = csv.writer(f)

            # Write the headers first
            writer.writerow(headers)

            for item in items:
                row = (item.get('itemId'), item.get('itemName'),
                       item.get('brand'), item.get('gtin'),
                       item.get('qty'), item.get('unit'),
                       item.get('price'), item.get('deliverableQty'),
                       lead_time, expiry,
                       Product.query.get(int(item.get('itemId'))).amazon_url,
                       Product.query.get(int(item.get('itemId'))).item_code,
                       Product.query.get(int(item.get('itemId'))).hs_code,
                       )

                writer.writerow(row)

        # Close the csv file when finished writing
        f.close()

        with open(file, mode="rb") as f:

            data = f.read()

        files = [("attachment",
                  (file_name, data))]

        msg = f'''
        Hello, this is an auto-email from swiftify. 
        {current_user.email} has sent you a quote. Please see attached. Thanks. 
        Your friends @ swiftify'''

        send_quote_or_request_via_email(msg=msg,
                                        subject=f"Someone sent you a quote "
                                                f"via email from {current_user.email}",
                                        recipients=[recipient, current_user.email],
                                        files=files)

        flash("Email has been sent successfully", category="success")

        return redirect(url_for('view_quote', quote_id=quote_id))

    context = dict(quote_id=quote.id,
                   items=items,
                   referrer=referrer,
                   lead_time=lead_time,
                   expiry=expiry,
                   form=send_email_form,
                   declined=quote.isDeclined,
                   reject_form=reject_form)

    return render_template("users/view_quote.html", **context)


@app.route('/user/export/quotes/data')
@login_required
def export_quotes():

    if current_user.role != "user":

        return redirect(url_for('vendor_app'))

    quotes = Quote.query.filter(Quote.buyer == current_user.email).all()

    # Construct a quotes 2 items key_value data store and join items as a single string
    quotes2items = {quote.id: ", ".join([i.get('itemName', "")
                    for i in json.loads(quote.items)]) for quote in quotes}

    file = None

    return send_file(file, as_attachment=True, mimetype="text/csv")


@app.route('/user/export/quote/<int:quote_id>')
@login_required
def export_quote(quote_id):

    if current_user.role != "user":

        return redirect(url_for('vendor_app'))

    quote = Quote.query.get(int(quote_id))

    data = json.loads(quote.items)

    lead_time = quote.lead_time

    valid_until = quote.valid_until

    file_name = f"quote_id_{quote_id}_" + str(uuid4()) + ".csv"

    file = str(Path(app.root_path) / 'cache' / 'user_exports' / file_name)

    headers = ("Item ID", "Name", "Brand",
               "Barcode / GTIN / EAN", "Requested Quantity", "Unit",
               "vendor price exw €", "Deliverable Quantity", "Lead time - working days",
               "valid until", "amazon url", "item code",
               "hs code")

    with open(file, mode="w", encoding="utf8") as f:
        writer = csv.writer(f)

        # Write the headers first
        writer.writerow(headers)

        for item in data:
            row = (item.get('itemId'), item.get('itemName'),
                   item.get('brand'), item.get('gtin'),
                   item.get('qty'), item.get('unit'),
                   item.get('price'), item.get('deliverableQty'),
                   lead_time, valid_until,
                   Product.query.get(int(item.get('itemId'))).amazon_url,
                   Product.query.get(int(item.get('itemId'))).item_code,
                   Product.query.get(int(item.get('itemId'))).hs_code,
                   )

            writer.writerow(row)

    # Close the csv file when finished writing
    f.close()

    return send_file(file, as_attachment=True, mimetype="text/csv")


@app.route("/convert/quote/to/<int:quote_id>/po", methods=["GET", "POST"])
@login_required
def convert_quote_2_po(quote_id):

    if current_user.role != "user":

        return redirect(url_for('vendor_app'))

    quote = Quote.query.get(int(quote_id))

    # if a po already exists from this quote
    if PO.query.filter_by(quote_id=quote_id).first():

        flash("You have already converted this quote to a Purchase Order")

        return redirect(url_for('view_quote', quote_id=quote_id))

    # create a new Purchase Order from this quote
    po = PO()

    po.items = quote.items
    po.req_id = quote.req_id
    po.quote_id = quote_id

    db.session.add(po)
    db.session.commit()

    return str(po.id)


@app.route("/user/reject/quote/<int:quote_id>", methods=["POST", "GET"])
@login_required
def user_reject_quote(quote_id):

    referrer = request.headers.get('Referer')

    if current_user.role != "user":

        return {"error": "access denied and you're not a user"}

    # status
    is_rejected = True

    quote = db.session.query(Quote).get(int(quote_id))

    quote.isDeclined = is_rejected

    # rejection committed to the database
    db.session.commit()

    '''
    Send vendor notify email and web message
    '''

    msg = f'''
            This might be heart-breaking. 
            Yes, your quote with ID {quote.id} has been rejected by the buyer. 
            Don't worry. Strive for the next quote then
        '''

    email_context = dict(full_name=quote.vendor,
                         msg=msg)

    # Email html template and content
    html = render_template("emails/quote_rejection_vendor.html",
                           **email_context)

    quote_rejection_vendor_email_alert(html=html,
                                       recipients=[quote.vendor],
                                       subject=f"your quote with ID {quote.id} has been rejected")
    # send web message
    send_web_msg(from_=quote.buyer,
                 to=quote.vendor,
                 text=msg,
                 kind="system")

    flash(f"You have rejected Quote {quote_id}", category="success")

    return redirect(referrer)


# user view rejected quotes
@app.route('/user/quotes/view/rejected')
@login_required
def user_rejected_quotes():

    if current_user.role != "user":

        return redirect(url_for('vendor_app'))

    quotes = Quote.query.filter(Quote.buyer == current_user.email,
                                Quote.isDeclined == True).all()

    # Construct a quotes 2 items key_value data store and join items as a single string
    quotes2items = {quote.id: ", ".join([i.get('itemName', "")
                    for i in json.loads(quote.items)]) for quote in quotes}

    context = dict(status="Rejected",
                   status_class="danger",
                   quotes=quotes,
                   quotes2items=quotes2items,
                   title="Drafted quotes",
                   format_datetime=format_datetime)

    return render_template("users/rejected_quotes.html", **context)
