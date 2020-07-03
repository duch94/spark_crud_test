from datetime import datetime
from typing import List

from flask import Blueprint, jsonify, request, json

from app.models.products import Product, Category, products_categories
from app import db

products_blueprint = Blueprint('products', __name__)


def create_or_get_categories(p: dict) -> List[Category]:
    """
    Func to get existing categories objects or create new otherwise
    :param p: payload of request
    :return: list of categories
    """
    recevied_categories: List[Category] = [Category(name=cat) for cat in p['categories']]
    categories = []
    for cat in recevied_categories:
        exists = db.session.query(db.exists().where(Category.name == cat.name)).all()[0][0]
        if exists:
            existing_category = Category.query.filter(Category.name == cat.name).all()[0]
            categories.append(existing_category)
        else:
            categories.append(cat)
    return categories


@products_blueprint.route('/products', methods=['GET'])
def get_products():
    return jsonify({
        'results': [p.serialized for p in Product.query.all()]
    })


@products_blueprint.route('/create_product', methods=['POST'])
def create_product():
    data = request.get_data().decode('utf-8')
    payload = json.loads(data)
    datetime_format = '%Y-%m-%d %H:%M:%S'

    if len(payload['categories']) < 1 or len(payload['categories']) > 5:
        return '{"status": "error", "msg": "categories number must be between 1 and 5"}', 400

    categories = create_or_get_categories(payload)

    try:
        new_prod = Product(name=payload['name'],
                           rating=float(payload['rating']),
                           featured=bool(payload['featured'] if 'featured' in payload.keys() else None),
                           expiration_date=(datetime.strptime(payload['expiration_date'], datetime_format)
                                            if ('expiration_date' in payload.keys()) else None),
                           brand_id=int(payload['brand_id']),
                           items_in_stock=int(payload['items_in_stock']),
                           receipt_date=(datetime.strptime(payload['receipt_date'], datetime_format)
                                         if ('receipt_date' in payload.keys()) else None))
    except TypeError as e:
        return '{"status": "error", "msg": "TypeError occured: check values of fields"}'
    except KeyError as e:
        return '{"status": "error", "msg": "field %s have not been found, but is required"}' % str(e), 400
    if new_prod.rating > 8.0:
        new_prod.featured = True
    [cat.products.append(new_prod) for cat in categories]
    [db.session.add(cat) for cat in categories]
    db.session.commit()
    return jsonify({"status": "ok", "msg": "product received"})


@products_blueprint.route('/update_product', methods=['PUT'])
def update_product():
    data = request.get_data().decode('utf-8')
    payload = json.loads(data)
    datetime_format = '%Y-%m-%d %H:%M:%S'

    product = Product.query.filter(Product.id == payload['id'])
    if product:
        if 'name' in payload.keys():
            product.update({'name': payload['name']})
        if 'featured' in payload.keys():
            product.update({'featured': bool(payload['featured'])})
        if 'rating' in payload.keys():
            product.update({'rating': float(payload['rating'])})
            if product.rating > 8.0:
                product.featured = True
        if 'items_in_stock' in payload.keys():
            product.update({'items_in_stock': int(payload['items_in_stock'])})
        if 'receipt_date' in payload.keys():
            product.update({'receipt_date': datetime.strptime(payload['receipt_date'], datetime_format)})
        if 'brand' in payload.keys():
            product.update({'brand': int(payload['brand'])})
        if 'categories' in payload.keys():
            categories = create_or_get_categories(payload)
            db.session.query(products_categories).filter(
                products_categories.c.product_id == int(payload['id'])).delete(synchronize_session=False)
            product_obj = product.all()[0]
            [cat.products.append(product_obj) for cat in categories]
            [db.session.add(cat) for cat in categories]
        if 'expiration_date' in payload.keys():
            product.update({'expiration_date': datetime.strptime(payload['expiration_date'], datetime_format)})

        db.session.commit()
        return jsonify({"status": "ok", "msg": "product updated"})
    else:
        return '{"status": "error", "msg": "no product found with given id"}', 404


@products_blueprint.route('/delete_product', methods=['DELETE'])
def delete_product():
    data = request.get_data().decode('utf-8')
    p = json.loads(data)

    products_result = Product.query.filter(Product.id == int(p['id'])).delete(synchronize_session=False)
    products_categories_result = db.session.query(products_categories).filter(
        products_categories.c.product_id == int(p['id'])).delete(synchronize_session=False)
    db.session.commit()
    if products_result == 1:
        return jsonify({"status": "ok",
                        "msg": "product deleted, also %d product_categories relations deleted"
                               % products_categories_result})
    else:
        return jsonify({"status": "warning", "msg": "%d products deleted, also %d product_categories relations deleted"
                                                    % (products_result, products_categories_result)})
