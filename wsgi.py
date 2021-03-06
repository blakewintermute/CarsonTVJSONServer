"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

application = get_wsgi_application()
"""

from flask import Flask, request, make_response
import json
import requests
import time
from copy import deepcopy as dc
import ast
import os

app = Flask(__name__)

def updateUPS(list):
    UPS = {}
    for server in list:
        try:
            r = requests.get(server + "/list")
            UPS[server] = set(r.json()["titles"])
        except:
            pass
    return UPS

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
        headers = request.headers.get('Access-Control-Request-Headers')
        if headers:
            response.headers['Access-Control-Allow-Headers'] = headers
    return response
app.after_request(add_cors_headers)

try:
    with open(os.path.join("data", "titles.json"),"r") as f:
        titleList = json.load(f)
    with open(os.path.join("data", "userData.json"),"r") as f:
        userData = json.load(f)
except:
    pass

@app.route('/json')
def get_json():
    userID = request.args.get("UserID")

    if userID not in userData:
        return userID + " is not a User", 401

    myServers = userData[userID]["servers"]

    UPS = updateUPS(myServers)

    if userData[userID]["type"] == "developer" or userData[userID]["type"] == "admin":
        uTL = list(titleList.keys())
    else:
        uTL = userData[userID]["titles"]

    titles = {}
    for id in uTL:
        titles[id] = dc(titleList[id])
        location = ""
        for server in UPS:
            if id in UPS[server]:
                location = server + "/media/" + id
                break
        titles[id]["location"] = location
        if location == "":
            titles.pop(id)

    r = make_response(json.dumps({"titles":titles, "pdata":userData[userID]["pdata"]}))
    r.headers['Access-Control-Allow-Origin'] = "*"
    return r


@app.route('/update', methods=['POST'])
def updateProgress():
    r = request.get_data()
    r = str(r)[2:-1]
    update = json.loads(r)
    uid = update["UserID"]

    if uid not in userData:
        return str(uid) + ' is not a user', 401

    id = update["id"]
    if titleList[id]["type"] == "series":
        cS = update["cS"]
        cE = update["cE"]
        if id not in userData[uid]["pdata"]:
            userData[uid]["pdata"][id] = {"cE":0, "cS":0, "map":{}}

        userData[uid]["pdata"][id]["cS"] = cS
        userData[uid]["pdata"][id]["cE"] = cE

        if str(cS) not in userData[uid]["pdata"][id]["map"]:
            userData[uid]["pdata"][id]["map"][str(cS)] = {}

        userData[uid]["pdata"][id]["map"][str(cS)][str(cE)] = update["progress"]
    else:
        userData[uid]["pdata"][id] = update["progress"]

    with open(os.path.join("central", "userData.json"), "w") as f:
        json.dump(userData, f)
    return '', 200

@app.route('/help')
def help():
    return str(os.listdir())


@app.route('/')
def default():
    return "Hi, this is the JSON server for CarsonTV"

if __name__ == "__main__":
    app.run(debug=True, host= '0.0.0.0', port=8081)
