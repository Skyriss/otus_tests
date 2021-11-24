import datetime
import hashlib
import json
import random
from unittest import TestCase, mock
import fakeredis

from parameterized import parameterized

import api
import req
from store import Store, Storage

INTERESTS = ["cars", "pets", "travel", "hi-tech", "sport", "music",
             "books", "tv", "cinema", "geek", "otus"]


class TestSuite(TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = Store(Storage())
        self.server = fakeredis.FakeServer()
        self.store.redis = fakeredis.FakeRedis(server=self.server)
        self.server.connected = True
        for i in range(10):
            self.store.cache_set("i:%i" % i,
                                 json.dumps(random.sample(INTERESTS, 2)))
            self.store.set("i:%i" % i,
                                 json.dumps(random.sample(INTERESTS, 2)))

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def set_valid_auth(self, request):
        if request.get("login") == req.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(bytes(datetime.datetime.now().strftime("%Y%m%d%H") + \
                                                    api.ADMIN_SALT, "utf-8")).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(bytes(msg, "utf-8")).hexdigest()

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @parameterized.expand([
        ("empty token",
         {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}}),
        ("wrong token",
         {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}}),
        ("empty token admin",
         {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}}),
    ])
    def test_bad_auth(self, case_name, request):
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @parameterized.expand([
        ("no arguments", {"account": "horns&hoofs", "login": "h&f", "method": "online_score"}),
        ("no method", {"account": "horns&hoofs", "login": "h&f", "arguments": {}}),
        ("no login", {"account": "horns&hoofs", "method": "online_score", "arguments": {}}),
    ])
    def test_invalid_method_request(self, case_name, request):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @parameterized.expand([
        ("empty request", {}),
        ("no email", {"phone": "79175002040"}),
        ("wrong first number in phone", {"phone": "89175002040", "email": "stupnikov@otus.ru"}),
        ("missing @ in email", {"phone": "79175002040", "email": "stupnikovotus.ru"}),
        ("wrong gender", {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1}),
        ("no bday", {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"}),
        ("too old bday", {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"}),
        ("wrong bday format", {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"}),
        ("wrong first name format",
         {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
          "first_name": 1}),
        ("wrong last name format",
         {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
          "first_name": "s", "last_name": 2}),
        ("no last name", {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"}),
        ("no phone", {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2}),
    ])
    def test_invalid_score_request(self, case_name, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @parameterized.expand([
        ("phone str and email", {"phone": "79175002040", "email": "stupnikov@otus.ru"}),
        ("phone int and email", {"phone": 79175002040, "email": "stupnikov@otus.ru"}),
        ("gender, bday, fname, lname", {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"}),
        ("gender and bday", {"gender": 0, "birthday": "01.01.2000"}),
        ("gender and bday", {"gender": 2, "birthday": "01.01.2000"}),
        ("fname and lname", {"first_name": "a", "last_name": "b"}),
        ("phone, email, gender, bday, fname, lname",
         {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
          "first_name": "a", "last_name": "b"}),
    ])
    def test_ok_score_request(self, chek_name, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @parameterized.expand([
        ("null", {}),
        ("client_ids missing", {"date": "20.07.2017"}),
        ("null client_ids", {"client_ids": [], "date": "20.07.2017"}),
        ("wrong client_ids type", {"client_ids": {1: 2}, "date": "20.07.2017"}),
        ("wrong client_ids items type", {"client_ids": ["1", "2"], "date": "20.07.2017"}),
        ("wrong date format", {"client_ids": [1, 2], "date": "XXX"}),
    ])
    def test_invalid_interests_request(self, case_name, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @parameterized.expand([
        ("ok values with func", {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")}),
        ("ok values", {"client_ids": [1, 2], "date": "19.07.2017"}),
        ("ok values wo date", {"client_ids": [0]}),
    ])
    def test_ok_interests_request(self, case_name, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(
            all(v and isinstance(v, list) and all(isinstance(i, str) for i in v) for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))
