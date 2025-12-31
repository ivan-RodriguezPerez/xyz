from flask import Flask, render_template, request
import subprocess


app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello world!'

@app.route('/speak', methods=['POST'])
def speak():
    text = request.get_json()

    subprocess.run(["espeak-ng", text])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
