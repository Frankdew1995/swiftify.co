import requests
import json
from pprint import pprint
from textblob import TextBlob

from pathlib import Path

from redislite import Redis

from app import app, db
from app.models import User
from app.aux_models import Message

from glob import glob
import os
import pandas as pd
from datetime import datetime
import pdfkit
from jinja2 import Environment, FileSystemLoader

from config import is_prod


class EmailService(object):

    pass


def subscribe_user(email):

    r = requests.post(
            "https://api.mailgun.net/v3/lists/subscribers.swiftify@bot.frankdu.co/members",
            auth=('api', 'xxx'),
            data={'subscribed': True,
                  'address': email})
    return r


def api_email_alert():

    r = requests.post(

        # Here goes your Base API URL
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        # Authentication part - A Tuple
        auth=("api", "key-xxxx"),

        # mail data will be used to send emails
        data={"from": "API Break Alert <bot@frankdu.co>",
              "to": ["frank.du@cnfrien.com"],
              "subject": "DM Data API seems broken",
              "text": "Hey, Frank. DM Data API seems broken. Please take care of this."}
    )

    return r


def vendor_signup_email_alert(msg, subject, files):

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        files=files,

        data={
            "from": "Vendor sign up alert <bot@bot.frankdu.co>",
            "to": "frank@frankdu.co",
            "subject": subject,
            "text": msg
        })

    print(r.status_code)

    return r


def send_quote_or_request_via_email(msg,
                                    subject,
                                    files,
                                    recipients):

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        files=files,

        data={
            "from": "swiftify send quote via email <bot@bot.frankdu.co>",
            "to": recipients,
            "subject": subject,
            "text": msg
        })

    print(r.status_code)

    return r


def user_signup_email_alert(msg, subject):

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        data={
            "from": "User sign up alert <bot@bot.frankdu.co>",
            "bcc": "frank@frankdu.co",
            "subject": subject,
            "text": msg
        })

    return r


def quote_received_email_alert(html, subject, recipients):

    '''
    :param html: the email body of html
    :param subject: the email subject
    :param recipients: list obj with several emails
    :return: the response of the post request
    '''

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        data={
            "from": "Quote Received Confirmation  <bot@bot.frankdu.co>",
            "to": recipients,
            "cc": ["frank.du@cnfrien.com"],
            "subject": subject,
            "html": html
        })

    print(r.status_code)

    return r


def quote_update_email_alert(html, subject, recipients):

    '''
    :param html: the email body of html
    :param subject: the email subject
    :param recipients: list obj with several emails
    :return: the response of the post request
    '''

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        data={
            "from": "Quote Update Notification  <bot@bot.frankdu.co>",
            "to": recipients,
            "cc": ["frank.du@cnfrien.com"],
            "subject": subject,
            "html": html
        })

    print(r.status_code)

    return r


def request_vendor_email_alert(html, subject, recipients):

    '''
    :param html: the email body
    :param subject: the email subject
    :param recipients: list obj with several emails
    :return: the response of the post request
    '''

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        data={
            "from": "new quote request notification <bot@bot.frankdu.co>",
            "to": recipients,
            "cc": "frank.du@cnfrien.com",
            "subject": subject,
            "html": html
        })

    print(r.status_code)

    return r


def quote_rejection_vendor_email_alert(html, subject, recipients):

    '''
    :param html: the email body
    :param subject: the email subject
    :param recipients: list obj with several emails
    :return: the response of the post request
    '''

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        data={
            "from": "quote rejection notification <bot@bot.frankdu.co>",
            "to": recipients,
            "bcc": "frank.du@cnfrien.com",
            "subject": subject,
            "html": html
        })

    print(r.status_code)

    return r


def user_confirmation_email(html, subject, recipients):

    '''
    :param html: the email body
    :param subject: the email subject
    :param recipients: list obj with several emails
    :return: the response of the post request
    '''

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        data={
            "from": "account verification <ops@flow.exhausted.one>",
            "to": recipients,
            "bcc": "frank.du@cnfrien.com",
            "subject": subject,
            "html": html
        })

    return r


def send_password_reset_email(html,
                              subject,
                              user):


    '''
    :param html: the email body
    :param subject: the email subject
    :param user: user object from model
    :return: the response of the post request
    '''

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        data={
            "from": "password reset Swiftify <bot@bot.frankdu.co>",
            "to": user.email,
            "bcc": "frank.du@cnfrien.com",
            "subject": subject,
            "html": html
        })

    return r


def email_invoice(subject, from_,
                  to, message,
                  files, **kwargs):

    data = {
            "from": f"{from_} <bot@bot.frankdu.co>",
            "to": to,
            "bcc": "frank.du@cnfrien.com",
            "subject": subject,
            "text": message,
        }

    if "cc" in kwargs.keys():

        data['cc'] = kwargs['cc']

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        files=files,

        data=data)
    print(r)
    return r


def search_by_ean(ean):

    dm_data_api = f"https://services.dm.de/product/DE/products/gtins/{ean}"

    raw = requests.get(dm_data_api).text

    data = json.loads(raw)

    if len(data) > 0:

        return data[0]

    else:

        print("no data")

        return []


def search_by_key(key):

    dm_search_api = f"https://services.dm.de/product/DE/products/search?sort=relevance&pageSize=500&q={key}"

    r = requests.get(dm_search_api)

    # if status code is not 200: send the email alert
    if r.status_code != 200:

        api_email_alert()

    raw = r.text

    data = json.loads(raw)

    products = data.get("products")

    pprint(products)

    return data.get("products")


def chain_amazon_query_url(name):

    blob = TextBlob(name)

    k = None

    if len(blob.words) > 1:

        k = "+".join(blob.words)

    else:

        k = name

    amazon_query_url = f"https://www.amazon.de/s?k={k}&ref=nb_sb_noss"

    print(amazon_query_url)

    return amazon_query_url


# Redis class
class RedisCache(object):

    def __init__(self, redis_path):

        self.redis_path = redis_path
        self.redis_conn = Redis(self.redis_path)

    def set_k(self, k, v):

        self.redis_conn.set(k, v)

        return self.redis_conn.set(k, v)

    def exists(self, k):

        return self.redis_conn.exists(k)

    def push_l(self, k, lst):

        self.redis_conn.rpush(k, *lst)

        return self.redis_conn.rpush(k, *lst)

    def get_v(self, k):

        v = self.redis_conn.get(k)

        v = v.decode("utf-8")

        return v

    def delete_k(self, k):

        if self.exists(k):

            v = self.redis_conn.delete(k)

            print(v)

            return v

    def keys(self):

        print(self.redis_conn.keys())

        return self.redis_conn.keys()

    def sort(self):

        return self.redis_conn.sort("desc")

    def close(self):

        self.redis_conn.close()


class JsonCache(object):

    def __init__(self, store_path):

        self.store_path = store_path

    def set_k(self, k, v):

        with open(self.store_path, "r") as store:

            data = store.read()

        data = json.loads(data)

        # add a new key-value pair
        data[k] = v

        with open(self.store_path, "w") as store_in:

            json.dump(data, store_in)

    def exists(self, k):

        with open(self.store_path, "r") as store:
            data = store.read()

        data = json.loads(data)

        keys = data.keys()

        return k in keys

    def get_v(self, k):

        with open(self.store_path, "r") as store:
            data = store.read()

        data = json.loads(data)

        # add a new key-value pair
        v = data.get(k)

        return v

    def delete_k(self, k):

        with open(self.store_path, "r") as store:

            data = store.read()

        data = json.loads(data)

        # pop this key from the dict despite it's existence
        data.pop(k, None)

        with open(self.store_path, "w") as store_in:

            json.dump(data, store_in, indent=2)


def query_products(query):

    blob = TextBlob(query)

    tokenized_words = blob.words

    # if the search contains more than one word
    if len(tokenized_words) > 1:

        tokenized_words.append(query)

        for word in tokenized_words:

            products_by_term = Product.query.filter(Product.name.contains(word)).all()

            products_by_gtin = Product.query.filter(Product.gtin.contains(word)).all()

            product_by_categories = Product.query.filter(Product.category.contains(word)).all()

            product_by_brands = Product.query.filter(Product.brand.contains(word)).all()

            product_by_item_codes = Product.query.filter(Product.item_code.contains(word)).all()

            products = products_by_gtin + products_by_term + \
                       product_by_categories + product_by_brands \
                       + product_by_item_codes

            return products

    else:

        products_by_term = Product.query.filter(Product.name.contains(query)).all()

        products_by_gtin = Product.query.filter(Product.gtin.contains(query)).all()

        product_by_categories = Product.query.filter(Product.category.contains(query)).all()

        product_by_brands = Product.query.filter(Product.brand.contains(query)).all()

        product_by_item_codes = Product.query.filter(Product.item_code.contains(query)).all()

        products = products_by_gtin + products_by_term \
                   + product_by_categories + product_by_brands \
                   + product_by_item_codes

        return products


def import_img_from_dm_by_brand(ean):

    searched_products = search_by_key("profissimo")

    for item in searched_products:
        product = Product()

        product.name = item.get('name')
        product.brand = "profissimo"
        product.is_available = item.get("purchasable")
        product.price = float(item.get('price'))
        product.gtin = item.get('gtin')
        product.origin = item.get('isoCountry')
        product.img = item.get('links')[0].get('href')
        product.vendor = json.dumps(["kogb@dm.de"])

        db.session.add(product)

        db.session.commit()

        return ean


def activate_vendor_account(vendor_email):

    vendor = db.session.query(User).filter_by(email=vendor_email).first()

    if vendor:

        vendor.activated = True
        db.session.commit()

    print(vendor.activated)


def remove_user_exports_uploads():

    docs = glob(str(Path(app.root_path) / 'cache' / 'user_exports' / '*.csv'))

    pdfs = glob(str(Path(app.root_path) / 'cache' / 'vendor_uploads' / '*.pdf'))

    files = docs + pdfs

    for file in files:

        try:
            os.remove(file)

        except Exception as e:

            print(f"Failed to remove file {file}")

            print(str(e))

        print(f"Removed {file}")


def html2pdf(html, pdf):

    # switching pdf engine when env varies.
    if is_prod:

        from weasyprint import HTML

        HTML(string=html).write_pdf(pdf)

    else:

        pdfkit.from_string(html, pdf)

    return pdf


def get_image_file_as_base64_data(file_path):

    import base64

    # reading in rb mode and decode in the end
    with open(file_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode()


def send_web_msg(from_, to, kind, text):

    message = Message()

    message.owner = to

    # system/user
    message.kind = kind
    message.content = text
    message.container = json.dumps({"from": from_})

    db.session.add(message)

    db.session.commit()

    print(message)


def calculate_palletization(item_id, api_key, subdomain):

    item_ = f"https://{api_key}:x@{subdomain}.salesbinder.com/api/2.0/items/{item_id}.json"

    item_desc = requests.get(item_).json().get("item").get("description").splitlines()

    palletized_data = [item_.split(":") for item_ in item_desc]

    # Init a palletization data dict
    palletization = {}

    for info in palletized_data:
        palletization[info[0].strip()] = int(info[1].strip())

    return palletization


def request_freight_quote(domain_name, api_key,
                          from_, to,
                          cc, attachment_name,
                          format, file_path,
                          origin, arrival, name,
                          ):

    timestamp = datetime.today().strftime("%Y-%B-%-d-%-H:%-M:%-S")

    return requests.post(
        f"https://api.mailgun.net/v3/{domain_name}/messages",
        auth=("api", api_key),

        # If sending several files, then pass serveral tuples in this list
        files=[("attachment", (f"{attachment_name}_{timestamp}.{format}",
                               open(file_path, "rb").read()))],

        data={
            "from": from_,
            "to": to,
            "cc": cc,
            "subject": f"New Air Quotation Request {timestamp}, from {origin} to {arrival}, Airport2Airport",
            "text": f'''

            Dear {name}, 

            Please find attached cargo info for quotation requests. 

            Please quote us the price with the following information as well: 

            Flight details: ETD, and ETA
            Cut-off date

            Your friends @ Swiftify

            '''
        })


def import_pos_from_salesbinder(api_key, subdomain):

    documents_api = f"https://{api_key}:x@{subdomain}.salesbinder.com/api/2.0/documents.json?contextId=11"

    documents_r = requests.get(documents_api)

    purchase_orders = documents_r.json().get("documents")[0]

    return purchase_orders


def return_currencies():

    from pathlib import Path

    currencies = Path(app.root_path) / "cache" / "Common-Currency.json"

    with open(str(currencies), "r") as c:

        raw_data = c.read()

    data = json.loads(raw_data)

    choices = [

        (i[0], i[1].get("name")) for i in data.items()

    ]

    return choices


from forex_python.converter import CurrencyCodes


def get_currency_symbol(currency_code):
    c = CurrencyCodes()
    symbol = c.get_symbol(currency_code)
    return symbol


def po_messenger(html, subject,
                 recipients,
                 cc_recipients,
                 sender_name):

    """
    :param cc_recipients: list of emails
    :param sender_name: custom defined according to
    context's UUID or context Name: PO / Invoice / Shipment / Sales Order
    :param html: the email body
    :param subject: the email subject
    :param recipients: list obj with several emails
    :return: the response of the post request
    """

    r = requests.post(
        "https://api.mailgun.net/v3/bot.frankdu.co/messages",

        auth=("api", "key-xxxxx"),

        data={
            "from": f"{sender_name} <messenger@flow.exhausted.one>",
            "to": recipients,
            "cc": cc_recipients,
            "bcc": "frank.du@cnfrien.com",
            "subject": subject,
            "html": html
        })

    return r
