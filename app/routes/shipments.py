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


@app.route('/user/app/shipments', methods=["GET", "POST"])
@login_required
def logistics():

    return render_template("users/logistics.html")


@app.route('/user/app/shipment/new', methods=["GET", "POST"])
@login_required
def new_shipment():

    form = AddAccountForm()

    if request.method == "POST":

        # convert String to Python dict
        data = json.loads(request.form.get('hidden-air-cargo-data'))

        stackable = request.form.get("stackable")

        customs_clearance = request.form.get("customs")

        export_documents = request.form.get("export-documents")

        num_of_hs_codes = request.form.get('hs-codes')

        flash("A freight quote will be automatically delivered to your inbox in 30 mins. "
              "Please stay tuned!")

        print(stackable, data)

        return jsonify({"data": data,
                        "customs_clearance":  customs_clearance,
                        "export_documents": export_documents,
                        "num_of_hs_codes": num_of_hs_codes,
                        "stackable": stackable})

        # return redirect(url_for('logistics'))

    return render_template("users/new_shipment.html", form=form)
