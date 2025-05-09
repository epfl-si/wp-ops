from flask import Flask, request

app = Flask(__name__)

@app.route('/', defaults={'path': ''}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route('/<path:path>', methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def catch_all(path):
    print(f"{request.method} {request.path}")
    print(request.headers)
    print(request.get_data().decode())
    return 'OK', 200

app.run(port=8083)
