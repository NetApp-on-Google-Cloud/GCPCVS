# -*- coding: utf-8 -*-

import requests
import base64, json, logging, sys
from google.auth.transport.requests import Request as googleRequest
from google.auth.jwt import Credentials
from google.oauth2 import service_account
from pathlib import Path

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

    def __init__(self, sa_key):
        """ Initialize token

        Args:
            sa_key (str): service account key with cloudvolumes.* permissions
                Either specify file path to JSON key file or pass key as base64-encoded string

        It raises a ValueError if key provided isn't a valid JSON key.
        """
        audience = 'https://cloudvolumesgcp-api.netapp.com'
        # check if we got passed a path to a service account JSON key file
        # or we got passed the key itself encoded base64
        if isBase64(sa_key):
            # we got passed an base64 encoded JSON key
            json_key = json.loads(base64.b64decode(sa_key))
        else:
            # we got passed an file path to an JSON key file
            file_path = Path(sa_key)
            if file_path.is_file():
                with open(file_path, 'r') as file:
                    json_key = json.loads(file.read())
            else:
                logging.error('Passed credentials are not a base64 encoded json key nor a vaild file path to a keyfile.')
                raise ValueError('Passed credentials are not a base64 encoded json key nor a vaild file path to a keyfile.')
        svc_creds = service_account.Credentials.from_service_account_info(json_key)
        jwt_creds = Credentials.from_signing_credentials(svc_creds, audience=audience)
        jwt_creds.refresh(googleRequest())

        # Extract projectID from JSON key and store it for later use
        self.credentials = jwt_creds
        self.projectID = json_key['project_id']

    def __call__(self, r):
        if self.credentials.expired:
            self.credentials.refresh(googleRequest())
        r.headers["authorization"] = "Bearer " + self.credentials.token.decode('utf-8')
        return r

    def __str__(self):
        if self.credentials.expired:
            self.credentials.refresh(googleRequest())
        return self.credentials.token.decode('utf-8')

    def getProjectID(self):
        """ Returns projectID fetched from JSON key """
        return self.projectID
