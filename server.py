from flask import Flask, json, request, render_template
import pathlib
import sqlite3
import logging
import typing
import dataclasses
from werkzeug.exceptions import HTTPException, BadRequest
import requests
import appsecrets

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler("server_logs.txt"),
                    logging.StreamHandler()
                ])


@dataclasses.dataclass
class Score:
    name: str
    difficulty: typing.Literal["Beginner", "Intermediate", "Expert"]
    seconds : int
    unix_time: int
    uuid_str: str

class DataStore:
    def __init__(self, dbpath):
        self._dbpath = pathlib.Path(dbpath)
        self._con = None

    def __enter__(self):
        if not self._dbpath.exists():
            logging.info(
                "database file does not exist: {}, creating tables".format(self._dbpath))
            self._con = sqlite3.connect(str(self._dbpath))
            self._create_tables()
        else:
            self._con = sqlite3.connect(str(self._dbpath))
        return self

    def __exit__(self, typ, value, traceback):
        self._con.close()

    def _create_tables(self):
        cur = self._con.cursor()
        # SQLLite automatically creates a `rowid` integer column.
        # uuid_str is expected to be a UUID created in the browser with `crypto.randomUUID()`. Example: 'e1748dc1-3882-4b2b-8c5d-fb72a151a2cf'
        cur.execute(
            "CREATE TABLE scores (name VARCHAR(255), difficulty VARCHAR(32), seconds INTEGER, unix_time INTEGER, uuid_str CHAR(32) PRIMARY KEY)")

    def scores_get_top_100(self, difficulty: str) -> typing.List[Score]:
        if not self._con:
            raise Exception(
                "self._con is not initialized. Try wrapping in a `with` statement")
        cur = self._con.cursor()
        res: typing.List[Score] = []
        
        cur = cur.execute("SELECT * FROM scores WHERE difficulty=:difficulty ORDER BY seconds ASC LIMIT 100", {"difficulty": difficulty})
        for row in cur:
            res.append(Score(*row))
        return res

    def score_add(self, s : Score) -> None:
        if not self._con:
            raise Exception(
                "self._con is not initialized. Try wrapping in a `with` statement")
        self._con.execute("INSERT INTO scores" + \
                                "(name, difficulty, seconds, unix_time, uuid_str)" + \
                                "VALUES(:name, :difficulty, :seconds, :unix_time, :uuid_str)",
                                dataclasses.asdict(s))
        self._con.commit()

    # For internal use only (e.g. removing foul language)
    def score_delete_by_uuid(self, uuid_str: str) -> int:
        if not self._con:
            raise Exception(
                "self._con is not initialized. Try wrapping in a `with` statement")
        cur = self._con.execute("DELETE FROM scores WHERE uuid_str=:uuid_str", {"uuid_str": uuid_str})
        self._con.commit()
        return cur.rowcount
    
    def scores_has_uuid(self, uuid_str: str) -> bool:
        if not self._con:
            raise Exception(
                "self._con is not initialized. Try wrapping in a `with` statement")
        cur = self._con.execute("SELECT COUNT(*) FROM scores WHERE uuid_str=:uuid_str", {"uuid_str": uuid_str})
        count = cur.fetchone()[0]
        return count > 0
    
app = Flask(__name__)

def _get_datastore() -> DataStore:
    if app.config.get("TESTING"):
        return DataStore("test.db")
    return DataStore("data.db")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit", methods=["post"])
def submit():

    testOnlyDoNotSave = False
    if "testOnlyDoNotSave" in request.json:
        testOnlyDoNotSave = request.json["testOnlyDoNotSave"]
        del request.json["testOnlyDoNotSave"]
        if "recaptchaToken" in request.json:
            del request.json["recaptchaToken"]

    if not app.config.get("TESTING") and not testOnlyDoNotSave:
        # Require a reCaptcha token.
        if "recaptchaToken" not in request.json:
            raise BadRequest("Required recaptchaToken was not sent")
        recaptchaToken = request.json["recaptchaToken"]
        url = "https://www.google.com/recaptcha/api/siteverify"
        data = {
            "secret": appsecrets.recaptchaSecretKey,
            "response" : recaptchaToken,
            "remoteip" : request.remote_addr
        }
        try:
            resp = requests.post(url, data=data)
        except Exception as exc:
            return {"ok": 0, "description": "Failed to verify reCaptcha token: {}".format(exc)} 
        
        try:
            score = resp.json()["score"]
        except Exception as exc:
            return {"ok": 0, "description": "Failed to read score from reCaptcha response: {}. Response={}".format(exc, resp.text)} 
        
        # From https://developers.google.com/recaptcha/docs/v3#interpreting_the_score:
        # "By default, you can use a threshold of 0.5."
        if score < .5:
            return {"ok": 0, "description": "reCaptcha token did not have high enough score. Try refreshing the page and submitting again."}
        
        del request.json["recaptchaToken"]

    try:
        s = Score(**request.json)
    except TypeError as te:
        raise BadRequest("Bad arguments: {}".format(str(te)))
    
    if testOnlyDoNotSave:
        return {"ok": 1, "description": "Testing. Not persisting"}

    with _get_datastore() as ds:
        if ds.scores_has_uuid(s.uuid_str):
            return {"ok": 0, "description": "Score already saved" }
        ds.score_add(s)
    return {"ok": 1}

@app.route("/get_top_100", methods=["get"])
def get():
    with _get_datastore() as ds:
        return {
            "ok": 1,
            "Beginner": ds.scores_get_top_100("Beginner"),
            "Intermediate": ds.scores_get_top_100("Intermediate"),
            "Expert": ds.scores_get_top_100("Expert")
        }

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "ok": 0,
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response