class ConferenceExists(BaseException):
    pass


class UserExists(BaseException):
    pass


class ConferenceDoesNotExist(BaseException):
    pass


class UserDoesNotExist(BaseException):
    pass


class NoSlotsInConference(BaseException):
    pass


class ConferenceAlreadyStarted(BaseException):
    pass


class BookingDoesNotExist(BaseException):
    pass


class TimeToConfirmBookingExceeded(BaseException):
    pass
