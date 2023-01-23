import requests
import json
import logging
from uuid import UUID
from .models import WalletPublicDid, CreatePresentationResponse
from ..config import settings
from .config import AgentConfig, MultiTenantAcapy, SingleTenantAcapy

_client = None
logger = logging.getLogger(__name__)

WALLET_DID_URI = "/wallet/did/public"
CREATE_PRESENTATION_REQUEST_URL = "/present-proof/create-request"
PRESENT_PROOF_RECORDS = "/present-proof/records"


class AcapyClient:
    acapy_host = settings.ACAPY_ADMIN_URL
    service_endpoint = settings.ACAPY_AGENT_URL

    wallet_token: str = None
    agent_config: AgentConfig

    def __init__(self):
        if settings.ACAPY_TENANCY == "multi":
            self.agent_config = MultiTenantAcapy()
        elif settings.ACAPY_TENANCY == "single":
            self.agent_config = SingleTenantAcapy()
        else:
            logger.warning("ACAPY_TENANCY not set, assuming SingleTenantAcapy")
            self.agent_config = SingleTenantAcapy()

        if _client:
            return _client
        super().__init__()

    def create_presentation_request(
        self, presentation_request_configuration: dict
    ) -> CreatePresentationResponse:
        logger.debug(f">>> create_presentation_request")
        present_proof_payload = {"proof_request": presentation_request_configuration}

        resp_raw = requests.post(
            self.acapy_host + CREATE_PRESENTATION_REQUEST_URL,
            headers=self.agent_config.get_headers(),
            json=present_proof_payload,
        )
        assert resp_raw.status_code == 200, resp_raw.content
        resp = json.loads(resp_raw.content)
        result = CreatePresentationResponse.parse_obj(resp)

        logger.debug(f"<<< create_presenation_request")
        return result

    def get_presentation_request(self, presentation_exchange_id: UUID):
        logger.debug(f">>> get_presentation_request")

        resp_raw = requests.get(
            self.acapy_host
            + PRESENT_PROOF_RECORDS
            + "/"
            + str(presentation_exchange_id),
            headers=self.agent_config.get_headers(),
        )
        assert resp_raw.status_code == 200, resp_raw.content
        resp = json.loads(resp_raw.content)

        logger.debug(f"<<< get_presentation_request -> {resp}")
        return resp

    def verify_presentation(self, presentation_exchange_id: UUID):
        logger.debug(f">>> verify_presentation")

        resp_raw = requests.post(
            self.acapy_host
            + PRESENT_PROOF_RECORDS
            + "/"
            + str(presentation_exchange_id)
            + "/verify-presentation",
            headers=self.agent_config.get_headers(),
        )
        assert resp_raw.status_code == 200, resp_raw.content
        resp = json.loads(resp_raw.content)

        logger.debug(f"<<< verify_presentation -> {resp}")
        return resp

    def get_wallet_public_did(self) -> WalletPublicDid:
        logger.debug(f">>> get_wallet_public_did")

        resp_raw = requests.get(
            self.acapy_host + WALLET_DID_URI,
            headers=self.agent_config.get_headers(),
        )
        assert (
            resp_raw.status_code == 200
        ), f"{resp_raw.status_code}::{resp_raw.content}"
        resp = json.loads(resp_raw.content)
        public_did = WalletPublicDid.parse_obj(resp["result"])

        logger.debug(f"<<< get_wallet_public_did -> {public_did}")
        return public_did
