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


@app.route('/user/view/invoices')
@login_required
def view_invoices():

    # only see thyself's invoices - can't view other users' invoices
    invoices = Invoice.query.filter(
        Invoice.sender == current_user.email).all()

    status2badge = {"Overdue": "warning",
                    "Sent": "info",
                    "Paid": "success",
                    "Draft": "primary"
                    }

    context = dict(invoices=invoices,
                   status2badge=status2badge)

    return render_template("users/view_invoices.html", **context)


@app.route('/user/create/invoice', methods=["POST", "GET"])
@login_required
def user_create_invoice():

    invoices = Invoice.query.all()

    today = str(int(datetime.today().timestamp()))

    try:

        invoice_id = max([invoice.id for invoice in invoices])

        invoice_number = "INV." + today + "-" + str(invoice_id)

    except Exception as e:

        print(str(e))

        invoice_number = "INV." + today + "-" + str(1)

    form = SendInvoiceForm()

    form.subject.data = f"Your Invoice For Order {invoice_number} From {current_user.company_name}"

    # user sends the invoice
    if form.validate_on_submit():

        from_ = form.from_.data
        to = form.to.data
        cc = form.cc.data
        subject = form.subject.data
        message = form.message.data

        invoice_number = form.invoice_id.data

        invoice = db.session.query(Invoice).get(invoice_number)

        # change invoice status to "Sent"

        invoice.status = "Sent"

        db.session.commit()

        # Pathlib object
        pdf_invoice = Path(app.root_path) / 'cache' / 'invoices' / f'{invoice_number}.pdf'

        # if the pdf invoice doesn't exist > generate a new one
        if not pdf_invoice.exists():

            settings = json.loads(current_user.container).get('settings')

            address = settings.get("address") + ", " + settings.get('city') + ", " + settings.get(
                'zip_code') + ", " + settings.get('country')

            logo_name = json.loads(current_user.container).get('settings').get('logo')

            logo_path = str(Path(app.root_path) / 'static' / 'img' / 'user_logos' / logo_name)

            img_string = get_image_file_as_base64_data(file_path=logo_path)

            email_context = dict(invoice_number=invoice_number,
                                 items=json.loads(invoice.items),
                                 total=invoice.total,
                                 subtotal=invoice.subtotal,
                                 discount=invoice.discount,
                                 shipping_charges=invoice.shipping_charges,
                                 tax=round(invoice.total - invoice.subtotal, 2),
                                 dated=invoice.timeCreated,
                                 due=invoice.dueUntil,
                                 customer_notes=json.loads(invoice.container).get('customer_notes'),
                                 img_string=img_string,
                                 company_name=current_user.company_name,
                                 address=address)

            html = render_template("invoice.html", **email_context)

            pdf = str(Path(app.root_path) /
                      'cache' / 'invoices' / f'{invoice_number}.pdf')

            # convert the html string to PDF
            html2pdf(html=html,
                     pdf=pdf)

            pdf_invoice = pdf

        with open(str(pdf_invoice), mode="rb") as f:

            data = f.read()

        attachment_name = f'{invoice_number}.pdf'

        files = [("attachment",
                  (attachment_name, data))]

        # finally send the email with invoice pdf file
        email_invoice(subject=subject,
                      from_=from_,
                      to=to,
                      message=message,
                      files=files,
                      cc=cc)

        flash(f"Great! Invoice {invoice_number} has been sent!", category="success")

        return redirect(url_for('view_invoices'))

    print(form.errors)

    # handles the ajax call in the end here.
    if request.method == "POST":

        data = request.json

        invoice_number = data.get('invoiceId')

        invoice = Invoice.query.get(invoice_number)

        if not invoice:

            # invoice doesn't exist and create a new
            invoice = Invoice()
            invoice.invoice_number = invoice_number

            invoice.timeCreated = datetime.strptime(data.get('dated'), "%Y-%m-%d")

            try:

                invoice.dueUntil = datetime.strptime(data.get('dueDate'), "%Y-%m-%d")

            except Exception as e:

                print(str(e))

                invoice.dueUntil = datetime.strptime(data.get('dated'), "%Y-%m-%d")

            invoice.items = json.dumps(data.get('data'))
            invoice.sender = data.get('invoiceSender')
            invoice.receiver = data.get('customer')
            invoice.discount = float(data.get('discount'))
            invoice.subtotal = float(data.get('subtotal'))
            invoice.shipping_charges = float(data.get('shippingCharges'))
            invoice.total = float(data.get('finalTotal'))
            invoice.status = data.get('status')
            invoice.container = json.dumps({"customer_notes":
                                            data.get('customerNotes')})

            invoice.terms = int(data.get('terms', 0))

            db.session.add(invoice)
            db.session.commit()

        else:

            # only updates the invoice
            invoice.timeCreated = datetime.strptime(data.get('dated'), "%Y-%m-%d")

            try:

                invoice.dueUntil = datetime.strptime(data.get('dueDate'), "%Y-%m-%d")

            except Exception as e:

                print(str(e))

                invoice.dueUntil = datetime.strptime(data.get('dated'), "%Y-%m-%d")

            invoice.items = json.dumps(data.get('data'))
            invoice.sender = data.get('invoiceSender')
            invoice.receiver = data.get('customer')
            invoice.discount = float(data.get('discount'))
            invoice.subtotal = float(data.get('subtotal'))
            invoice.shipping_charges = float(data.get('shippingCharges'))
            invoice.total = float(data.get('finalTotal'))
            invoice.status = data.get('status')
            invoice.container = json.dumps({"customer_notes":
                                            data.get('customerNotes')})

            invoice.terms = int(data.get('terms', 0))

            db.session.commit()

        print(request.json)

        return request.json

    context = dict(invoice_number=invoice_number,
                   form=form)

    return render_template("users/create_invoice.html", **context)


@app.route('/view/invoice/<string:invoice_number>')
@login_required
def view_invoice(invoice_number):

    invoice = Invoice.query.get(invoice_number)
    try:

        tax_amount = round((invoice.total - invoice.subtotal), 2)

    except Exception as e:

        print(str(e))

        tax_amount = ""

    context = dict(invoice_number=invoice_number,
                   referrer=request.headers.get('Referer'),
                   items=json.loads(invoice.items),
                   customer=invoice.receiver,
                   dated=invoice.timeCreated,
                   due=invoice.dueUntil,
                   terms=invoice.terms,
                   customer_notes=json.loads(invoice.container).get('customer_notes'),
                   subtotal=invoice.subtotal,
                   discount=invoice.discount,
                   shipping_charges=invoice.shipping_charges,
                   total=invoice.total,
                   tax_amount=tax_amount)

    return render_template("users/view_invoice.html", **context)


@app.route('/edit/invoice/<string:invoice_number>')
@login_required
def edit_invoice(invoice_number):

    invoice = Invoice.query.get(invoice_number)

    try:

        tax_amount = round((invoice.total - invoice.subtotal), 2)

    except Exception as e:

        print(str(e))

        tax_amount = ""

    context = dict(invoice_number=invoice_number,
                   referrer=request.headers.get('Referer'),
                   items=json.loads(invoice.items),
                   customer=invoice.receiver,
                   dated=invoice.timeCreated,
                   due=invoice.dueUntil,
                   terms=invoice.terms,
                   customer_notes=json.loads(invoice.container).get('customer_notes'),
                   subtotal=invoice.subtotal,
                   discount=invoice.discount,
                   shipping_charges=invoice.shipping_charges,
                   total=invoice.total,
                   tax_amount=tax_amount)

    return render_template("users/edit_invoice.html", **context)


@app.route('/export/invoice/as/pdf/<string:invoice_number>')
@login_required
def export_invoice(invoice_number):

    invoice = Invoice.query.get(invoice_number)

    settings = json.loads(current_user.container).get('settings')

    address = settings.get("address") + ", " + settings.get('city') + ", " + settings.get('zip_code') + ", " + settings.get('country')

    logo_name = json.loads(current_user.container).get('settings').get('logo')

    logo_path = str(Path(app.root_path) / 'static' / 'img' / 'user_logos' / logo_name)

    img_string = get_image_file_as_base64_data(file_path=logo_path)

    context = dict(invoice_number=invoice_number,
                   items=json.loads(invoice.items),
                   total=invoice.total,
                   subtotal=invoice.subtotal,
                   discount=invoice.discount,
                   shipping_charges=invoice.shipping_charges,
                   tax=round(invoice.total - invoice.subtotal, 2),
                   dated=invoice.timeCreated,
                   due=invoice.dueUntil,
                   customer_notes=json.loads(invoice.container).get('customer_notes'),
                   img_string=img_string,
                   company_name=current_user.company_name,
                   address=address
                   )

    html = render_template("invoice.html", **context)

    pdf = str(Path(app.root_path) /
              'cache' / 'invoices' / f'{invoice_number}.pdf')

    # convert the html string to PDF
    html2pdf(html=html,
             pdf=pdf)

    return send_file(pdf, as_attachment=True)


@app.route('/sourcing/database', methods=["GET", "POST"])
@login_required
def database():

    void_keys = db.session.query(SearchKey).filter_by(name="none")
    # remove search keys like "none" or ""
    if void_keys:

        for search_key in void_keys:

            db.session.delete(search_key)

            db.session.commit()

    common_entities = SearchKey.query.order_by(desc(SearchKey.counts)).limit(10).all()

    common_searches = [entity.name for entity in common_entities]

    context = dict()

    if request.method == "POST":

        keyword = request.form.get('search')

        if keyword:

            keyword = keyword.strip()

        context['query'] = keyword

        return redirect(url_for('render_search_results', query=keyword))

    context["common_searches"] = common_searches

    return render_template("users/database.html", **context)


@app.route('/search/query/<string:query>', methods=["POST", "GET"])
def render_search_results(query):

    # Query all searched terms from redis
    searched_terms = [term.name for term in SearchKey.query.all()]

    if request.method == "POST":

        keyword = request.form.get('search').strip()

        # If this term never searched > caching it
        if keyword.lower() not in searched_terms:

            new_term = SearchKey()
            new_term.name = keyword.lower()
            new_term.counts = 1
            db.session.add(new_term)
            db.session.commit()

        else:

            term = SearchKey.query.filter_by(name=keyword.lower()).first()
            term.counts = term.counts + 1
            db.session.commit()

        return redirect(url_for('render_search_results', query=keyword))

    products = query_products(query)

    num_results = len(products)

    # If this term never searched > caching it
    if query.lower() not in searched_terms:

        new_term = SearchKey()
        new_term.name = query.lower()
        new_term.counts = 1
        db.session.add(new_term)
        db.session.commit()

    else:

        term = SearchKey.query.filter_by(name=query.lower()).first()
        term.counts = term.counts + 1
        db.session.commit()

    context = dict(products=list(products),
                   num_results=num_results,
                   query=query)

    return render_template("users/query_results.html", **context)

