#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, jsonify, request, make_response, render_template
from flask_restful import Api, Resource, reqparse
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class Restaurants(Resource):
    def get(self):
        response_dict_list = [item.to_dict() for item in Restaurant.query.all()]
        return make_response(jsonify(response_dict_list), 200)

class RestaurantDetail(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        
        if restaurant is None:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)

        response_dict = {
            "id": restaurant.id,
            "address": restaurant.address,
            "name": restaurant.name,
            "restaurant_pizzas": []
        }
        
        for item in restaurant.restaurant_pizza:
            pizza = item.pizza
            response_dict["restaurant_pizzas"].append({
                "id": item.id,
                "pizza": {
                    "id": pizza.id,
                    "ingredients": pizza.ingredients,
                    "name": pizza.name
                },
                "pizza_id": item.pizza_id,
                "price": item.price,
                "restaurant_id": item.restaurant_id
            })
        
        response = make_response(jsonify(response_dict), 200)
        return response
    
    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant is None:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)

        db.session.delete(restaurant)
        db.session.commit()
        return '', 204

class Pizzas(Resource):
    def get(self):
        response_data = [item.to_dict() for item in Pizza.query.all()]
        return make_response(jsonify(response_data), 200)

class RestaurantPizzas(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('price', type=int, required=True, help="Price cannot be blank and must be an integer")
        parser.add_argument('pizza_id', type=int, required=True, help="Pizza ID cannot be blank")
        parser.add_argument('restaurant_id', type=int, required=True, help="Restaurant ID cannot be blank")
        args = parser.parse_args()

        if not (1 <= args['price'] <= 30):
            return {"errors": ["validation errors"]}, 400

        pizza = Pizza.query.get(args['pizza_id'])
        restaurant = Restaurant.query.get(args['restaurant_id'])

        if not pizza or not restaurant:
            return {"errors": ["Invalid pizza_id or restaurant_id"]}, 400

        new_restaurant_pizza = RestaurantPizza(
            price=args['price'],
            pizza_id=args['pizza_id'],
            restaurant_id=args['restaurant_id']
        )

        try:
            db.session.add(new_restaurant_pizza)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"errors": ["validation errors"]}, 400

        response_data = {
            "id": new_restaurant_pizza.id,
            "price": new_restaurant_pizza.price,
            "pizza_id": new_restaurant_pizza.pizza_id,
            "restaurant_id": new_restaurant_pizza.restaurant_id,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            },
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            }
        }

        return make_response(jsonify(response_data), 201)
    
api.add_resource(Restaurants, '/restaurants')
api.add_resource(RestaurantDetail, '/restaurants/<int:id>')
api.add_resource(Pizzas, '/pizzas')
api.add_resource(RestaurantPizzas, '/restaurant_pizzas')


if __name__ == "__main__":
    app.run(port=5555, debug=True)