import logging

from pymongo.database import Database
from urllib.parse import urlparse
from jwkest.jwk import rsa_load, RSAKey, KEYS

from pyop.authz_state import AuthorizationState
from pyop.provider import Provider
from pyop.subject_identifier import HashBasedSubjectIdentifierFactory
from pyop.userinfo import Userinfo


from api.core.config import settings

logger = logging.getLogger(__name__)

issuer_url = settings.CONTROLLER_URL
if urlparse(issuer_url).scheme != "https":
    logger.error("CONTROLLER_URL is not HTTPS. changing openid-config for development")
    issuer_url = issuer_url[:4] + "s" + issuer_url[4:]
signing_key = RSAKey(
    key=rsa_load(settings.SIGNING_KEY_FILENAME), use="sig", alg="RS256"
)
signing_keys = KEYS().append(signing_key)

# config from vc-authn-oidc 1.0 can be found here
# https://toip-vc-authn-controller-dev.apps.silver.devops.gov.bc.ca/.well-known/openid-configuration

# TODO validate the correctness of this? either change config or add capabilities
configuration_information = {
    "issuer": issuer_url,
    "authorization_endpoint": f"{issuer_url}/authorization",
    "token_endpoint": f"{issuer_url}/token",
    "jwks_uri": f"{issuer_url}/.well-known/openid-configuration/jwks",
    "response_types_supported": ["code", "id_token", "token"],
    "id_token_signing_alg_values_supported": [signing_key.alg],
    "response_modes_supported": ["fragment", "query", "form_post"],
    "subject_types_supported": ["public"],
    "grant_types_supported": ["hybrid"],
    "claim_types_supported": ["normal"],
    "claims_parameter_supported": True,
    "claims_supported": ["sub"],
    "request_parameter_supported": True,
    "request_uri_parameter_supported": False,
    "scopes_supported": ["openid", "profile"],
    "token_endpoint_auth_methods_supported": ["client_secret_basic"],
    "frontchannel_logout_supported": True,
    "frontchannel_logout_session_supported": True,
    "backchannel_logout_supported": True,
    "backchannel_logout_session_supported": True,
}

subject_id_factory = HashBasedSubjectIdentifierFactory(settings.SUBJECT_ID_HASH_SALT)

# placeholder that gets set on app_start and write operations to ClientConfigurationCRUD
provider = None


async def init_provider(db: Database):
    global provider
    from api.clientConfigurations.crud import ClientConfigurationCRUD

    all_kc_configs = await ClientConfigurationCRUD(db).get_all()
    client_configs = {d.client_name: d.dict() for d in all_kc_configs}

    provider = Provider(
        signing_key,
        configuration_information,
        AuthorizationState(subject_id_factory),
        client_configs,
        Userinfo({"Jason": {"sub": "Jason"}}),
    )