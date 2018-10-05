import datetime
import typing

from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authentication import extract_http_basic_credentials
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.request import Request
from zope.interface import implementer
import transaction
from tracim_backend.exceptions import UserDoesNotExist
from tracim_backend.lib.core.user import UserApi
from tracim_backend.models import User

BASIC_AUTH_WEBUI_REALM = "tracim"
TRACIM_API_KEY_HEADER = "Tracim-Api-Key"
TRACIM_API_USER_EMAIL_LOGIN_HEADER = "Tracim-Api-Login"


def _get_auth_unsafe_user(
    request: Request,
    email: str=None,
    user_id: int=None,
) -> typing.Optional[User]:
    """
    :param request: pyramid request
    :return: User or None
    """
    app_config = request.registry.settings['CFG']
    uapi = UserApi(None, session=request.dbsession, config=app_config)
    try:
        _, user = uapi.find(user_id=user_id, email=email)
        return user
    except UserDoesNotExist:
        return None

###
# Pyramid HTTP Basic Auth
###


@implementer(IAuthenticationPolicy)
class TracimBasicAuthAuthenticationPolicy(BasicAuthAuthenticationPolicy):

    def __init__(self, realm):
        BasicAuthAuthenticationPolicy.__init__(self, check=None, realm=realm)
        # TODO - G.M - 2018-09-21 - Disable callback is needed to have BasicAuth
        # correctly working, if enabled, callback method will try check method
        # who is now disabled (uneeded because we use directly
        # authenticated_user_id) and failed.
        self.callback = None

    def authenticated_userid(self, request):
        # check if user is correct
        credentials = extract_http_basic_credentials(request)
        user = _get_auth_unsafe_user(
            request,
            email=request.unauthenticated_userid
        )
        if not user \
                or user.email != request.unauthenticated_userid \
                or not user.is_active \
                or user.is_deleted \
                or not credentials \
                or not user.validate_password(credentials.password):
            return None
        return user.user_id

from pyramid_ldap import (
    get_ldap_connector,
    groupfinder,
    )

@implementer(IAuthenticationPolicy)
class LDAPBasicAuthAuthenticationPolicy(BasicAuthAuthenticationPolicy):

    def __init__(self, realm):
        BasicAuthAuthenticationPolicy.__init__(self, check=None, realm=realm)
        # TODO - G.M - 2018-09-21 - Disable callback is needed to have BasicAuth
        # correctly working, if enabled, callback method will try check method
        # who is now disabled (uneeded because we use directly
        # authenticated_user_id) and failed.
        self.callback = None

    def authenticated_userid(self, request):
        # check if user is correct
        credentials = extract_http_basic_credentials(request)

        connector = get_ldap_connector(request)
        print(vars(connector))
        data = connector.authenticate(
            request.unauthenticated_userid,
            credentials.password
        )
        user = None
        print(data)
        #print (data is not None and isinstance(data[1], dict))
        if data:
            ldap_data = data[1]

            user = _get_auth_unsafe_user(
                request,
                email=request.unauthenticated_userid
            )
            if not user:
                app_config = request.registry.settings['CFG']
                uapi = UserApi(None, session=request.dbsession, config=app_config)
                user = uapi.create_user(
                    email = ldap_data['mail'][0],
                    password = ldap_data['userpassword'][0],
                    name = ldap_data['givenname'][0],
                    do_save = True,
                    do_notify = False
                )
                transaction.commit()

        # or not user.validate_password(credentials.password)
        if not user \
                or user.email != request.unauthenticated_userid \
                or not user.is_active \
                or user.is_deleted \
                or not credentials:

            return None
        return user.user_id


###
# Pyramid cookie auth policy
###


@implementer(IAuthenticationPolicy)
class CookieSessionAuthentificationPolicy(SessionAuthenticationPolicy):

    def __init__(self, reissue_time: int, debug: bool = False):
        SessionAuthenticationPolicy.__init__(self, debug=debug, callback=None)
        self._reissue_time = reissue_time
        self.callback = None

    def authenticated_userid(self, request):
        # check if user is correct
        user = _get_auth_unsafe_user(request, user_id=request.unauthenticated_userid)  # nopep8
        # do not allow invalid_user + ask for cleanup of session cookie
        if not user or not user.is_active or user.is_deleted:
            request.session.delete()
            return None
        # recreate session if need renew
        if not request.session.new:
            now = datetime.datetime.now()
            last_access_datetime = datetime.datetime.utcfromtimestamp(request.session.last_accessed)  # nopep8
            reissue_limit = last_access_datetime + datetime.timedelta(seconds=self._reissue_time)  # nopep8
            if now > reissue_limit:  # nopep8
                request.session.regenerate_id()
        return user.user_id

    def forget(self, request):
        """ Remove the stored userid from the session."""
        if self.userid_key in request.session:
            request.session.delete()
        return []


###
# Pyramid API key auth
###


@implementer(IAuthenticationPolicy)
class ApiTokenAuthentificationPolicy(CallbackAuthenticationPolicy):

    def __init__(self, api_key_header: str, api_user_email_login_header: str):
        self.api_key_header = api_key_header
        self.api_user_email_login_header = api_user_email_login_header
        self.callback = None

    def authenticated_userid(self, request):
        app_config = request.registry.settings['CFG']  # type:'CFG'
        valid_api_key = app_config.API_KEY
        api_key = request.headers.get(self.api_key_header)
        if not api_key or not valid_api_key:
            return None
        if valid_api_key != api_key:
            return None
        # check if user is correct
        user = _get_auth_unsafe_user(request, email=request.unauthenticated_userid)
        if not user or not user.is_active or user.is_deleted:
            return None
        return user.user_id

    def unauthenticated_userid(self, request):
        return request.headers.get(self.api_user_email_login_header)

    def remember(self, request, userid, **kw):
        return []

    def forget(self, request):
        return []
