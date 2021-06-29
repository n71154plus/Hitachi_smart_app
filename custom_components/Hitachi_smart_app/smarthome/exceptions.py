class HitachiBaseException(Exception):
    """ Base exception """


class HitachiRefreshTokenNotFound(HitachiBaseException):
    """ Refresh token not found """

    def __init__(
        self, message="Refresh token not existed. You may need to login again."
    ):
        super().__init__(message)
        self.message = message


class HitachiTokenExpired(HitachiBaseException):
    """ Token expired """


class HitachiInvalidRefreshToken(HitachiBaseException):
    """ Refresh token expired """


class HitachiLoginFailed(HitachiBaseException):
    """ Any other login exception """
