"""Infer Google API credentials based on runtime environment"""

import os
from google.oauth2 import credentials, service_account
from google.auth import impersonated_credentials, default

TARGET_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


class Credentials:  # pylint: disable=too-few-public-methods
    """Detect, (generate) and return appropriate credentials"""

    def __init__(self) -> None:
        """
        Determine authentication method based on environment. All options
        rely on OAuth 2.0 access tokens; however for `SA` and `User` we
        need to explicitly acquire the access token first.

        * SA: Service account authentication which uses the locally stored
        private key. Currently only used by Gitlab CI

        * User: User authentication which requires the user to authenticate
        with his/her/their Google Cloud account. Used for local development

        * None: Application default credentials (ADC): when running inside
        GCF, the App Engine Identity Credentials will be used
        """
        if "GOOGLE_OAUTH_ACCESS_TOKEN" in os.environ:
            self._auth_method = "User"
        elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            self._auth_method = "SA"
        else:
            self._auth_method = None

    def get(self) -> credentials.Credentials:
        """
        Return appropriate credentials
        """

        if self._auth_method == "User":
            # Runs `gcloud auth print-access-token` once again although re-using
            # GOOGLE_OAUTH_ACCESS_TOKEN also works. Due to the short lifetime
            # of the access tokens, the first method is preferred.
            source_credentials = credentials.UserAccessTokenCredentials()
        elif self._auth_method == "SA":
            source_credentials = service_account.Credentials.from_service_account_file(
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"], scopes=TARGET_SCOPES
            )
        else:
            creds, _ = default(scopes=TARGET_SCOPES)
            return creds

        target_credentials = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=f'terraform@{os.environ["PROJECT"]}.iam.gserviceaccount.com',
            target_scopes=TARGET_SCOPES,
            lifetime=300,
        )
        return target_credentials
