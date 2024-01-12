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
    key='x',
    secret='x',
    cluster='eu',
    ssl=True
)


@app.route('/api/messenger', methods=['POST'])
@login_required
def bound_messenger():

    data = request.get_json()
    context = data
    context['full_name'] = ""
    context['po_number'] = data.get('po_number', '')
    tenant = current_user.tenant

    recipients = []
    cc_recipients = []
    # if a specific user has been mentioned
    if data.get('mentioned_email'):
        recipients.append(data.get('mentioned_email'))
        # retrieve all users email for this tenant to copy in the email
        cc_recipients = [user.email for user in tenant.users]
        # add the mentioned user email into html email template
        context['full_name'] = data.get('mentioned_email')
    else:
        recipients = [user.email for user in tenant.users]

    # send the PO message
    html = render_template('emails/messenger.html',
                           **context)
    po_messenger(html=html,
                 subject=f"PO Messenger For PO {data.get('po_number', '')}",
                 recipients=recipients,
                 cc_recipients=cc_recipients,
                 sender_name=f"PO Messenger {context.get('tenant')}")

    return jsonify({'message': 'Email sent successfully'}), 200


