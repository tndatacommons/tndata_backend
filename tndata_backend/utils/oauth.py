from django.conf import settings
from oauth2client import client, crypt


def verify_token(token_string):
    """Verify the given Google auth token string & return the 'sub' portion
    as stated in the docs. See: https://goo.gl/MIKN9X

    Returns None upon failure.

    """
    token = None
    valid_accounts = ['accounts.google.com', 'https://accounts.google.com']
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    try:
        idinfo = client.verify_id_token(token, client_id)
        # TODO: If multiple clients access the backend server:
        # if idinfo['aud'] not in [ANDROID_ID, IOS_ID, client_id]:
        #     raise crypt.AppIdentityError("Unrecognized client.")
        if idinfo['iss'] not in valid_accounts:
            raise crypt.AppIdentityError("Wrong issuer.")

        # Save the portion we want to keep.
        token = idinfo['sub']

    except crypt.AppIdentityError:  # Invalid token
        token = None

    return token
