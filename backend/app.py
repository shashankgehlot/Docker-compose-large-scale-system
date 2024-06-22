from flask import Flask, jsonify
from pymongo import MongoClient
import psycopg2
import redis
import pika
from celery import Celery

app = Flask(__name__)

# MongoDB connection
mongo_client = MongoClient("mongodb://mongo:27017/")
mongo_db = mongo_client["mydatabase"]
mongo_collection = mongo_db["mycollection"]

# PostgreSQL connection
# postgres_conn = psycopg2.connect(
#     dbname="mydatabase",
#     user="postgres",
#     password="password",
#     host="postgres",
#     port="5432"
# )
# postgres_cursor = postgres_conn.cursor()

# Redis connection
redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

# RabbitMQ connection
rabbitmq_connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
rabbitmq_channel = rabbitmq_connection.channel()
rabbitmq_channel.queue_declare(queue='myqueue')

app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@app.route('/')
def index():
    return jsonify({
        "message": "Welcome to the Flask app!"
    })

@app.route('/mongo')
def mongo_test():
    # Insert a document into MongoDB
    mongo_collection.insert_one({"name": "test", "value": 123})
    doc = mongo_collection.find_one({"name": "test"})
    return jsonify({
        "message": "MongoDB test",
        "document": {
            "name": doc["name"],
            "value": doc["value"]
        }
    })

@app.route('/postgres')
def postgres_test():
    # Insert a row into PostgreSQL
    postgres_cursor.execute("CREATE TABLE IF NOT EXISTS test (id SERIAL PRIMARY KEY, name VARCHAR(50), value INT)")
    postgres_cursor.execute("INSERT INTO test (name, value) VALUES (%s, %s) RETURNING id", ("test", 123))
    postgres_conn.commit()
    postgres_cursor.execute("SELECT * FROM test WHERE name = %s", ("test",))
    row = postgres_cursor.fetchone()
    return jsonify({
        "message": "PostgreSQL test",
        "row": row
    })

@app.route('/redis')
def redis_test():
    # Set and get a value in Redis
    redis_client.set('test_key', 'test_value')
    value = redis_client.get('test_key')
    return jsonify({
        "message": "Redis test",
        "value": value.decode('utf-8')
    })

@app.route('/rabbitmq')
def rabbitmq_test():
    # Send and receive a message from RabbitMQ
    rabbitmq_channel.basic_publish(exchange='', routing_key='myqueue', body='Hello, RabbitMQ!')
    method_frame, header_frame, body = rabbitmq_channel.basic_get('myqueue', auto_ack=True)
    return jsonify({
        "message": "RabbitMQ test",
        "body": body.decode('utf-8')
    })

@celery.task
def add(x, y):
    return x + y

@app.route('/celery-task')
def celery_task():
    task = add.delay(10, 20)
    return jsonify({
        "message": "Celery task submitted",
        "task_id": task.id
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
