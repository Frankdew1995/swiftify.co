import os

cur_path = os.path.dirname(__file__)

basedir = os.path.abspath(cur_path)

url_query_string = "retryWrites=false"

is_prod = False


class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or '3ac74ee3-89b2-4dca-96a2-0e90cf34f847'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'dev.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = False

    CACHE_TYPE = "simple"

    DEBUG_RESPONSES = True

    MONGO_URI = "mongodb+srv://frankduco:YZw8BQMZ3xiii3DA@exhausteddotone.xn1vflz.mongodb.net/?retryWrites=true&w=majority"


class ProductionConfig(Config):

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')

    MONGO_URI = f"mongodb://quotemanager:quotemanager1@ds239928.mlab.com:39928/swiftify?{url_query_string}"

    REDIS_URI = ""

    DEBUG = False

