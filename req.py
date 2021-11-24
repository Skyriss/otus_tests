from field import (
    Field,
    ClientIDsField,
    DateField,
    CharField,
    EmailField,
    PhoneField,
    BirthDayField,
    GenderField,
    ArgumentsField,
)

ADMIN_LOGIN = "admin"

class RequestValidationFailedError(Exception):

    def __init__(self, err, message="Request validation failed: {}"):
        self.message = message.format(err)
        super().__init__(self.message)

class Request:

    def __init__(self):
        self.fields = [field for field, value in self.__class__.__dict__.items() if isinstance(value, Field)]

    def validate(self, kwargs):
        for field in self.fields:
            value = kwargs.get(field, None)
            setattr(self, field, value)

    def get_arguments(self):
        return {key: value for key, value in self.__class__.__dict__.items() if isinstance(value, Field)}


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self, kwargs):
        super().validate(kwargs)
        if not any([
            self.phone and self.email,
            self.first_name and self.last_name,
            self.gender is not None and self.birthday
        ]):
            raise RequestValidationFailedError("any of pairs expected: 'phone/email', 'first name/last name', 'gender/birthday'")


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN
