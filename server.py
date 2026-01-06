from flask import Flask, jsonify, request


app = Flask(__name__)


@app.route('/super')
def super():
    return jsonify(message="It's working"), 200


if __name__ == "__main__":
    app.run()
