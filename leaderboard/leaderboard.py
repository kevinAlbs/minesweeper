from flask import Flask

app = Flask(__name__)

@app.route("/submit", methods=["post"])
def submit():
    return {"ok": 0, "error": "not yet implemented"}

@app.route("/get", methods=["get"])
def get():
    raise Exception("Not yet implemented")