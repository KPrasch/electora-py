from typing import Optional, Dict
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from nucypher_core import ferveo

from nucypher.characters.lawful import Ursula, Bob
from nucypher.cli.utils import connect_to_blockchain
from nucypher.utilities.emitters import StdoutEmitter

# Networks

_GOERLI_URI = "https://goerli.infura.io/v3/663d60ae0f504f168b362c2bda60f81c"
_TEACHER_URI = "https://lynx.nucypher.network:9151"

# GraphQL

_ELECTORA_ARWEAVE_TAG = "electora/ballot/uuid"
_ARWEAVE_GQL_ENDPOINT = "https://arweave.net/graphql"  # TODO: Get this from somewhere else (config, env, round-robin, etc.)
_GET_ELECTION_VOTES_QUERY_TEMPLATE = """
query getElectionVotes {
    transactions(tags: [{ name: "$tagName", values: ["$electionId"] }]) {
        edges {
            node {
                id
            }
        }
    }
}
"""

BOB = Bob(
    eth_provider_uri=_GOERLI_URI,
    domain="lynx",
    known_nodes=[
        Ursula.from_teacher_uri(
            teacher_uri=_TEACHER_URI, min_stake=0, provider_uri=_GOERLI_URI
        )
    ],
)


def _fetch_vote_transactions(election_id: str, endpoint: Optional[str] = _ARWEAVE_GQL_ENDPOINT) -> Dict:
    """Fetches all arweave transactions tagged for a particular ballot ID."""
    transport = AIOHTTPTransport(url=endpoint)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    variables_map = {
        'transactions': {
            'tags': {'tagName': _ELECTORA_ARWEAVE_TAG, 'electionId': election_id}
        }
    }
    result = client.execute(
        gql(_GET_ELECTION_VOTES_QUERY_TEMPLATE),
        variable_values=variables_map
    )
    return result


def fetch_votes(election_id: str, endpoint: Optional[str] = _ARWEAVE_GQL_ENDPOINT):
    transactions = _fetch_vote_transactions(election_id=election_id, endpoint=endpoint)
    print(transactions)
    pass


def _get_conditions(timestamp):
    time_condition = {
        "method": "timelock",
        "returnValueTest": {"comparator": ">=", "value": timestamp},
    }
    return [time_condition]


def decrypt_vote(ciphertext, timestamp):
    connect_to_blockchain(eth_provider_uri=_GOERLI_URI, emitter=StdoutEmitter())
    BOB.start_learning_loop(now=True)
    cleartext = BOB.threshold_decrypt(
        ritual_id=0,
        ciphertext=ferveo.Ciphertext.from_bytes(bytes.fromhex(ciphertext)),
        conditions=_get_conditions(timestamp),
    )
    return bytes(cleartext).decode()


def verify_vote(vote):
    pass


def count_votes():
    pass
