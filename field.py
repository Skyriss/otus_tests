import datetime

UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}
NULLABLE = ['', {}, (), [], None]

class FieldEmptyValueError(Exception):

    def __init__(self, field_name, message="Field '{}' cannot have empty value"):
        self.message = message.format(field_name)
        super().__init__(self.message)

class FieldMissingError(Exception):

    def __init__(self, field_name, message="Field '{}' is required"):
        self.message = message.format(field_name)
        super().__init__(self.message)

class FieldValidationError(Exception):

    def __init__(self, message="Validation failed"):
        super().__init__(message)

class Field:
    _type = None

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self._name = None
        self._value = None

    def __set_name__(self, owner, name):
        self._name = name

    def __set__(self, owner, value):
        self._value = value
        self.validate()
        #owner.__dict__[self._name] = value

    def __get__(self, instance, owner):
        return self._value
        #return instance.__dict__[self._name]

    def _validate(self):
        pass

    def validate(self):
        if self.required and self._value is None:
            raise FieldMissingError("Field '{}' is required".format(self._name))
        if not self.nullable and self._value in NULLABLE:
            raise FieldEmptyValueError(self._name)
        if self._value and self._type:
            if not isinstance(self._value, self._type):
                raise FieldValidationError("Field '{}' must be '{}', but got '{}'".format(
                    self._name,
                    self._type,
                    type(self._value)
                ))
        if self._value:
            self._validate()


class CharField(Field):
    _type = str


class ArgumentsField(Field):
    _type = dict


class EmailField(CharField):
    _type = str

    def _validate(self):
        if '@' not in self._value or '.' not in self._value:
            raise FieldValidationError("Email must contain '@' and '.' symbols")


class PhoneField(Field):
    _type = (str, int)

    def _validate(self):
        self._value = str(self._value)
        if len(self._value) != 11:
            raise FieldValidationError("Phone number must be 11 digits long")
        if not self._value.startswith("7"):
            raise FieldValidationError("Phone number must start with '7'")
        if not self._value.isdigit():
            raise FieldValidationError("Phone number must contain only digits")


class DateField(Field):
    _type = str

    def _validate(self):
        try:
            self._value = datetime.datetime.strptime(self._value, "%d.%m.%Y")
            _ = self._value.strftime("%Y%m%d")
        except ValueError:
            raise FieldValidationError("Date field has wrong format. 'dd.mm.yyyy' expected")


class BirthDayField(DateField):
    _type = str

    def _validate(self):
        super()._validate()
        bday_year = self._value.year
        diff = datetime.datetime.now().year - bday_year
        if diff <= 0:
            raise FieldValidationError("Birthday is too close")
        if diff >= 70:
            raise FieldValidationError("Bithday is too far away")


class GenderField(Field):
    _type = int

    def _validate(self):
        if self._value not in GENDERS:
            raise FieldValidationError("Gender must be one of '{}', but got '{}'".format(GENDERS, self._value))


class ClientIDsField(Field):
    _type = list

    def _validate(self):
        if not all([isinstance(item, int) for item in self._value]):
            raise FieldValidationError("ClientIDs must be a list of int")
