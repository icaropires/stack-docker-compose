import os
import pika
from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics


DEBUG = True


app = Flask(__name__)
metrics = PrometheusMetrics(app)

metrics.info('app_devops', 'Information from application devops demonstration')

host = os.getenv("RABBITMQ_HOST", "localhost")
port = os.getenv("RABBITMQ_PORT", 5672)
queue = os.getenv("RABBITMQ_QUEUE", "hello")

# Avoiding bug when using __main__
#   https://github.com/rycus86/prometheus_flask_exporter/issues/40
os.environ["DEBUG_METRICS"] = "true" if DEBUG else "false"

html = """
<br>Type your favourite <i>pudim</i> flavour:
<br>
<form method='POST' action='/'>
    <input type='text' name='flavour'>
    <input type='submit'>
</form>
"""


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        app.logger.info(request.form.get("flavour"))
        enqueue(request.form.get("flavour"))
    return html


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


def enqueue(value):
    app.logger.info("Received message: %s", value)
    params = pika.ConnectionParameters(host=host, port=port)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    channel.basic_publish(exchange='', routing_key=queue, body=value)
    connection.close()
    app.logger.info("Enqueued message on host %s:%s queue %s: %s", host, port,
                    queue, value)


if __name__ == "__main__":
    app.run(debug=DEBUG, host="0.0.0.0", port=8000)
