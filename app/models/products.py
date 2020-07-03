import datetime

from flask_sqlalchemy import orm

from app import db


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.Unicode(50), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    featured = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    expiration_date = db.Column(db.DateTime, nullable=True)

    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    categories = db.relationship('Category', secondary='products_categories', backref='products')

    items_in_stock = db.Column(db.Integer, nullable=False)
    receipt_date = db.Column(db.DateTime, nullable=True)

    @property
    def serialized(self):
        return {
            'id': self.id,
            'name': self.name,
            'rating': self.rating,
            'featured': self.featured,
            'items_in_stock': self.items_in_stock,
            'receipt_date': self.receipt_date,
            'brand': self.brand.serialized,
            'categories': [c.serialized for c in self.categories],
            'expiration_date': self.expiration_date,
            'created_at': self.created_at
        }

    @orm.validates('name')
    def validate_name(self, key, name):
        assert isinstance(name, str)
        assert (len(name) > 0) and (len(name) <= 50)
        return name

    @orm.validates('categories')
    def validate_categories(self, key, categories):
        assert isinstance(categories, Category)
        return categories

    @orm.validates('expiration_date')
    def validate_expiration_date(self, key, expiration_date):
        if expiration_date is not None:
            datetime_format = '%Y-%m-%d %H:%M:%S'
            # exp_time_parsed = datetime.datetime.strptime(expiration_date, datetime_format)
            assert expiration_date > datetime.datetime.now() + datetime.timedelta(days=30)


class Brand(db.Model):
    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), nullable=False)
    country_code = db.Column(db.Unicode(2), nullable=False)

    products = db.relationship('Product', backref='brand')

    @property
    def serialized(self):
        return {
            'id': self.id,
            'name': self.name,
            'country_code': self.country_code
        }

    @orm.validates('name')
    def validate_name(self, key, name):
        assert isinstance(name, str)
        assert (len(name) > 0) and (len(name) <= 50)
        return name

    @orm.validates('country_code')
    def validate_country_code(self, key, country_code):
        assert isinstance(country_code, str)
        assert (len(country_code) > 0) and (len(country_code) <= 2)
        return country_code


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), nullable=False)

    @property
    def serialized(self):
        return {
            'id': self.id,
            'name': self.name,
        }

    @orm.validates('name')
    def validate_name(self, key, name):
        assert isinstance(name, str)
        assert (len(name) > 0) and (len(name) <= 50)
        return name


products_categories = db.Table('products_categories',
                               db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
                               db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
                               )
