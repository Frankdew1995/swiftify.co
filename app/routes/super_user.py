
from app import (app, render_template,
                 url_for, redirect,
                 request, make_response,
                 send_file, jsonify,
                 flash, session)

from flask_login import (login_required, login_manager,
                         login_user, logout_user,
                         current_user, )

from sqlalchemy import desc

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from app import db, mongo, login
from itsdangerous import URLSafeTimedSerializer


from app.forms import SubscribeForm, VendorSignUpForm, SignInForm, AddAccountForm

from app.utils import (subscribe_user, query_products,
                       vendor_signup_email_alert, request_vendor_email_alert,
                       quote_update_email_alert, quote_received_email_alert,
                       user_confirmation_email)

import json

from pathlib import Path

import csv
from uuid import uuid4
from datetime import datetime, timedelta

import json

from pathlib import Path

import csv
from uuid import uuid4
from datetime import datetime

import os
from pprint import pprint

from config import Config


# Some useful variables
date_format = "%Y-%m-%d"

datetime_format = "%Y.%m.%d %H:%M:%S"

# Serializer for generating random tokens
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


@app.route("/dash")
@login_required
def dash():

    if current_user.email != supers.get("3ac74ee3-89b2-4dca-96a2-0e90cf34f847").get("email"):

        return "you cannot access this page. Contact the lord - frank.du@cnfrien.com"

    return render_template("admins/index.html")


# view all freight forwarders
@app.route("/forwarders")
def view_forwarders():

    pass


@app.route("/add/forwarders", methods=["POST", "GET"])
def add_forwarder():

    forwarders_data = {

    }

    # with open("", "r") as store:
    #     data = store.read()
    #
    # data = json.loads(data)

    return jsonify({"status": "success"})



