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
                        Warehouse, Shipment, User, Activity)

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
    app_id='1182915',
    key='2da9c9700dd0922bfaa1',
    secret='9903a6e4f63bdb94856f',
    cluster='eu',
    ssl=True
)


@app.route("/post/activity", methods=["POST"])
@login_required
def post_activity():
    # The "type" of activity might need to be added to the form data on the front end.
    activity_type = request.form.get("activity-type")

    # checking if warehouse id exists
    warehouse_id = request.form.get("warehouse_id")

    # mentioned_user_email
    mentioned_user_email = request.form.get("mentionInput")

    activity = Activity(
        text=request.form.get("message"),
        sender_id=current_user.id,
        tenant_id=current_user.tenant_id,
        type=activity_type,
        po_id=int(request.form.get("po_id")),
        warehouse_id=int(warehouse_id) if warehouse_id else 0)

    try:
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        # Rollback in case of error
        db.session.rollback()
        print("Failed to add activity. Error: ", str(e))

    # Prepare data to be sent to Client / Browser
    data = {
        'senderName': current_user.user_name,
        'senderEmail': current_user.email,
        'text': activity.text,
        'timestamp': str(activity.timestamp),
        'tenant': activity.tenant.company_name,
        "po_uuid": request.form.get("po_uuid"),
        "po_number": request.form.get("po_number")
    }

    if mentioned_user_email:
        # sanitize and trim the email
        mentioned_email = mentioned_user_email.strip().lower()
        data['mentioned_email'] = mentioned_email

    # error handling when there's a conn issue
    try:
        # Trigger Pusher event
        pusher_client.trigger('activity-feed', 'activity-posted', data)
    except Exception as e:
        print(f'Failed to trigger Pusher event: {e}')
        return jsonify({"status": 404, "error": "Failed to trigger Pusher event"}), 404

    return jsonify({"status": 200})
