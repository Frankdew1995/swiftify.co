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


# route for caching user's wish list data in redis
@app.route('/user/add/product/<int:product_id>')
@login_required
def cache_product(product_id):

    product = Product.query.get(int(product_id))

    referrer = request.headers.get('Referer')

    if current_user.role != "user":

        return redirect(url_for('vendor_app'))

    user = User.query.get(int(current_user.id))

    flash(f"{product.name} has been added to your cart", category="success")

    # if user's cart not exists
    if not cart.exists(str(user.id)):

        products = [product_id]

        # key-value pair > convert it to String
        cart.set_k(user.id, products)

        return redirect(referrer)

    products = cart.get_v(str(user.id))

    if isinstance(products, list):

        products.append(product_id)

        # key-value pair > convert it to String
        cart.set_k(user.id, products)

    return redirect(referrer)


# remove product from cart by id or by all
@app.route("/remove/product/cache/<string:product_id>")
@login_required
def remove_product_cache(product_id):

    if current_user.role != "user":

        return redirect(url_for('vendor_app'))

    if product_id.lower() == "all":

        cart.delete_k(str(current_user.id))

        flash("all products removed from your cart", category="success")

        return redirect(url_for('view_cart'))

    # Querying the product in json cache
    product_ids = list(set(cart.get_v(str(current_user.id))))

    ident = int(product_id)

    # query the product that's been removed
    product = Product.query.get(int(product_id))

    if ident in product_ids:

        product_ids.remove(ident)

        # new list again dumped to json string in to Redis
        cart.set_k(current_user.id, product_ids)

        flash(f"{product.name} has been removed from your cart", category="success")

    return redirect(url_for('view_cart'))


@app.route('/user/view/cart')
@login_required
def view_cart():

    if current_user.role != "user":

        return redirect(url_for('vendor_app'))

    # Querying the product cache in redis
    if cart.exists(str(current_user.id)):

        product_ids = set(cart.get_v(str(current_user.id)))

        items = [Product.query.get(int(ident)) for ident in product_ids]

    else:

        # this user has no items in cart
        items = []

    context = dict(items=items)

    return render_template("users/view_cart.html", **context)


# ajax call for handling user's sourcing request from cart
@app.route("/users/requests/listen", methods=["POST"])
@login_required
def listen_user_request():

    data = request.json

    requester = data.get('requester')

    items = data.get('details')

    all_vendors = []

    for item in items:

        item_id = item.get('itemId')
        product = Product.query.get(item_id)

        if product:

            vendors = json.loads(product.vendor)
            all_vendors.extend(vendors)

    # all involved vendors
    all_vendors = set(all_vendors)

    for vendor in all_vendors:

        # init a new request object from db model
        req = Request()

        req.requester = requester
        req.owner = vendor

        # convert the list object to a string
        req.items = json.dumps(items)

        db.session.add(req)
        db.session.commit()

        try:

            # if the vendor id exists
            alias = vendor

        except Exception as e:

            print(str(e))
            # if the user is anonymous or not logged in
            alias = ""

        context = dict(full_name=alias)

        # send vendor an email
        # render the email templates
        html = render_template("emails/view_request.html", **context)

        request_vendor_email_alert(html=html,
                                   subject="New buyer products quotation request received!!",
                                   recipients=[vendor])

    # finally send the quote received confirmation email to the requester/ buyer
    quote_received_email_alert(html=render_template("emails/quote_received_confirmation.html"),
                               recipients=[requester],
                               subject="Your quote request has been received")

    return {"data": items}
