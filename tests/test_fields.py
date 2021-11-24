#!/usr/bin/env python3

from datetime import datetime, timedelta
from unittest import TestCase

from parameterized import parameterized

from field import (
    ArgumentsField,
    EmailField,
    CharField,
    Field,
    FieldValidationError,
    FieldEmptyValueError,
    FieldMissingError,
    PhoneField,
    DateField,
    BirthDayField,
    GenderField,
    ClientIDsField,
)


class TestFields(TestCase):
    next_day = datetime.now() + timedelta(days=1)
    previous_century = datetime.now() - timedelta(days=-36500)

    @parameterized.expand([
        ("Valid value required, nullable", True, True, "Lorem ipsum", None),
        ("Valid value required non-nullable", True, False, "Lorem ipsum", None),
        ("Valid value non-required nullable", False, True, "Lorem ipsum", None),
        ("Valid value non-required non-nullable", False, False, "Lorem ipsum", None),
        ("Empty value required, nullable", True, True, "", None),
        ("Empty value required non-nullable", True, False, None, FieldMissingError),
        ("Empty value non-required nullable", False, True, "", None),
        ("Empty value non-required non-nullable", False, False, None, FieldEmptyValueError),
        ("Empty value required, nullable", True, True, None, FieldMissingError),
        ("Empty value required non-nullable", True, False, None, FieldMissingError),
        ("Empty value non-required nullable", False, True, None, None),
        ("Empty value non-required non-nullable", False, False, None, FieldEmptyValueError),
    ])
    def test_Field(self, check_name, required, nullable, test_value, ex):
        if ex:
            with self.assertRaises(ex):
                cls = CharField(required=required, nullable=nullable).__set__(Field(), test_value)
        else:
            cls = CharField(required=required, nullable=nullable).__set__(Field(), test_value)

    @parameterized.expand([
        ("CharField valid value", CharField, "Lorem ipsum", None),
        ("CharField invalid value wrong type", CharField, 100500, FieldValidationError),
        ("ArgumentsField valid value", ArgumentsField, {"test": True}, None),
        ("ArgumentsField invalid value wrong type", ArgumentsField, 100500, FieldValidationError),
        ("EmailField valid value", EmailField, "a@mail.xx", None),
        ("EmailField invalid value wrong type", EmailField, 100500, FieldValidationError),
        ("EmailField invalid value missing dot", EmailField, "a@mailxx", FieldValidationError),
        ("EmailField invalid value missing @", EmailField, "amail.xx", FieldValidationError),
        ("PhoneField valid vaule str", PhoneField, "79876543210", None),
        ("PhoneField valid vaule int", PhoneField, 79876543210, None),
        ("PhoneField invalid value short", PhoneField, "79", FieldValidationError),
        ("PhoneField invalid value chars", PhoneField, "79876543XXX", FieldValidationError),
        ("DateField valid value", DateField, "31.12.2020", None),
        ("DateField invalid value wrong type", DateField, 100500, FieldValidationError),
        ("DateField invalid value wrong type", DateField, "20201231", FieldValidationError),
        ("BirthDayField valid value", BirthDayField, "01.01.1980", None),
        ("BirthDayField invalid value wrong type", BirthDayField, 100500, FieldValidationError),
        ("BirthDayField invalid value in future", BirthDayField, next_day.strftime("%d.%m.%Y"), FieldValidationError),
        ("BirthDayField invalid value in close past", BirthDayField, previous_century.strftime("%d.%m.%Y"),
         FieldValidationError),
        ("GenderField valid value male", GenderField, 1, None),
        ("GenderField valid value female", GenderField, 2, None),
        ("GenderField valid value unknown", GenderField, 0, None),
        ("GenderField invalid value wrong type", GenderField, "0", FieldValidationError),
        ("GenderField invalid value unknown value", GenderField, 100500, FieldValidationError),
        ("ClientIDsField valid value", ClientIDsField, [1, 2, 3], None),
        ("ClientIDsField invalid value wrong type", ClientIDsField, 100500, FieldValidationError),
        ("ClientIDsField invalid value wrong type inside list", ClientIDsField, ["1", "2", "3"], FieldValidationError),
    ])
    def test_Fields(self, check_name, cls, test_value, ex):
        if ex:
            with self.assertRaises(ex):
                inst = cls()
                inst._value = test_value
                self.assertIsNone(inst.validate())
        else:
            inst = cls()
            inst._value = test_value
            self.assertIsNone(inst.validate())
