#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import logging
# from scoring import get_score, get_interests
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser

import scoring
from field import (
    FieldMissingError,
    FieldValidationError,
    FieldEmptyValueError,
)
from req import (
    MethodRequest,
    OnlineScoreRequest,
    ClientsInterestsRequest,
    RequestValidationFailedError,
)
from store import Store, Storage

SALT = "Otus"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}


def check_auth(request):
    if request.is_admin:
        auth = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
        digest = hashlib.sha512(auth.encode("utf-8")).hexdigest()
    else:
        auth = request.account + request.login + SALT
        digest = hashlib.sha512(auth.encode("utf-8")).hexdigest()
    if digest == request.token:
        return True
    return False


def get_score(request, ctx, store):
    if isinstance(request, OnlineScoreRequest):
        return int(ADMIN_SALT) if ctx["is_admin"] else scoring.get_score(
            store,
            request.phone,
            request.email,
            request.birthday,
            request.gender,
            request.first_name,
            request.last_name
        )
    return 200


def online_score_handler(request, ctx, store):
    online_score_request = OnlineScoreRequest()
    online_score_request.validate(request.arguments)
    ctx["has"] = request.arguments
    score = get_score(online_score_request, ctx, store)
    return {"score": score}, OK


def clients_interests_handler(request, ctx, store):
    clients_interests_request = ClientsInterestsRequest()
    clients_interests_request.validate(request.arguments)
    interests = {client_id: scoring.get_interests(store, client_id) for client_id in
                 clients_interests_request.client_ids}
    ctx["nclients"] = len(clients_interests_request.client_ids)
    return interests, OK


def method_handler(request, ctx, store):
    methods = {
        "online_score": online_score_handler,
        "clients_interests": clients_interests_handler,
    }
    try:
        method_request = MethodRequest()
        method_request.validate(request.get("body"))
        ctx["is_admin"] = method_request.is_admin
        if not check_auth(method_request):
            return "Auth failed", FORBIDDEN
        response, code = methods[method_request.method](method_request, ctx, store)
    except (
    RequestValidationFailedError, FieldMissingError, FieldValidationError, FieldEmptyValueError) as err:
        error_message = "Sorry, your request contains errors: {}".format(err)
        logging.error(error_message)
        return error_message, INVALID_REQUEST
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = Store(Storage())
    store.connect()

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except (IOError, json.JSONDecodeError):
            code = BAD_REQUEST
        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s", self.path, data_string, context["request_id"])
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s", e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode("utf-8"))


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s", opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
