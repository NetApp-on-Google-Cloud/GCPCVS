# -*- coding: utf-8 -*-

import requests
import base64, json, logging, re, datetime
from google.auth.transport.requests import Request as googleRequest
from google.auth.jwt import Credentials
from google.oauth2 import service_account
from pathlib import Path
from google.cloud import iam_credentials_v1


def isBase64(sb):
    """ Checks weather the passed string is base64 encoded content or not """

    try:
            if isinstance(sb, str):
                    # If there's any unicode here, an exception will be thrown and the function will return false
                    sb_bytes = bytes(sb, 'ascii')
            elif isinstance(sb, bytes):
                    sb_bytes = sb
            else:
                    raise ValueError("Argument must be string or bytes")
            return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
            return False

class BearerAuth(requests.auth.AuthBase):
    """ Stores, passes und refreshes JWT tokens for CVS. Use with with requests 'auth' parameter. """
    credentials = None
    projectID = None

    def __init__(self, service_account_identifier):
        """ Initialize token

        Args:
            service_account_identifier (str): service account  with cloudvolumes.* permissions
                    Can be specified in multiple ways:
                    1. Absolute file path to an JSON key file
                    2. JSON key as base64-encoded string
                    3. Service Account principal name when using service account impersonation

        It raises a ValueError if key provided isn't a valid JSON key.
        """
        audience = 'https://cloudvolumesgcp-api.netapp.com'

        # Check if we got a passed a user-managed service account principal
        # Format: <service_account_name>@<project_id>.iam.gserviceaccount.com
        user_managed_sa_regex = "^[a-z]([-a-z0-9]*[a-z0-9])@[a-z0-9-]+\.iam\.gserviceaccount\.com$"
        if re.match(user_managed_sa_regex, service_account_identifier):
            self.projectID = service_account_identifier.split('@')[1].split('.')[0]
            self.credentials = self.ImpersonationCreds(service_account_identifier)
        else:
            # check if we got passed a path to a service account JSON key file
            # or we got passed the key itself encoded base64
            if isBase64(service_account_identifier):
                # we got passed an base64 encoded JSON key
                json_key = json.loads(base64.b64decode(service_account_identifier))
            else:
                # we got passed an file path to an JSON key file
                file_path = Path(service_account_identifier)
                if file_path.is_file():
                    with open(file_path, 'r') as file:
                        json_key = json.loads(file.read())
                else:
                    logging.error('Passed credentials are not a base64 encoded json key nor a vaild file path to a keyfile.')
                    raise ValueError('Passed credentials are not a base64 encoded json key nor a vaild file path to a keyfile.')

            self.projectID = json_key['project_id']
            self.credentials = self.JSONKeyCreds(json_key)

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.credentials.get_token()
        return r

    def __str__(self):
        return self.credentials.get_token()

    def getProjectID(self):
        """ Returns projectID fetched from JSON key """
        return self.projectID

    class ImpersonationCreds:
        # Internal helper class for Service Account Impersonation auth
        expiry = datetime.datetime.now()
        token = None
        service_account_name = None
        token_life_time = 15*60  # 15 Minutes

        def __init__(self, service_account_name: str):
            self.service_account_name = service_account_name
            self._new_token()

        def get_token(self) -> str:
            if datetime.datetime.now() + datetime.timedelta(seconds=10) > self.expiry:
                # Token to expire within 10s. Let's refresh
                self._new_token()
            return self.token

        def _new_token(self):
            audience = 'https://cloudvolumesgcp-api.netapp.com'

            now = datetime.datetime.now()
            self.expiry = now + datetime.timedelta(seconds = self.token_life_time)

            claims = {
                "iss": self.service_account_name,
                "sub": self.service_account_name,
                "iat": int(now.timestamp()),
                "exp": int(self.expiry.timestamp()),
                "aud": audience,
            }

            client = iam_credentials_v1.IAMCredentialsClient()
            service_account_path = client.service_account_path('-', self.service_account_name)
            response = client.sign_jwt(request = { "name": service_account_path, "payload": json.dumps(claims) })
            self.token = response.signed_jwt

    class JSONKeyCreds:
        # Internal helper class for JSON key auth
        credentials = None

        def __init__(self, json_key: str):
            audience = 'https://cloudvolumesgcp-api.netapp.com'

            svc_creds = service_account.Credentials.from_service_account_info(json_key)
            jwt_creds = Credentials.from_signing_credentials(svc_creds, audience=audience)
            jwt_creds.refresh(googleRequest())

            self.credentials = jwt_creds

        def get_token(self) -> str:
            if self.credentials.expired:
                self.credentials.refresh(googleRequest())
            return self.credentials.token.decode('utf-8')
