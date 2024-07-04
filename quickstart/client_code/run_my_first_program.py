import argparse
import asyncio
import py_nillion_client as nillion
import os
import sys
import pytest
import importlib

from py_nillion_client import NodeKey, UserKey
from dotenv import load_dotenv

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey

from nillion_python_helpers import get_quote_and_pay, create_nillion_client, create_payments_config
# from config import CONFIG_PROGRAM_NAME, CONFIG_PARTY_1, CONFIG_N_PARTIES

home = os.getenv("HOME")
load_dotenv(f"{home}/.config/nillion/nillion-devnet.env")

CONFIG_PROGRAM_NAME = "my_first_program"


# 1st party
CONFIG_PARTY_1 = {
    "seed": "party_3_seed",
    "party_name": "Party3",
    "secrets": {
        "my_int1": 1,
    },
}

# N other parties
CONFIG_N_PARTIES = [
    {
        "seed": "party_1_seed",
        "party_name": "Party1",
        "secret_name": "A",
        "secret_value": 10,
    },
    {
        "seed": "party_2_seed",
        "party_name": "Party2",
        "secret_name": "B",
        "secret_value": 5,
    },
]
async def main(args=None):
    cluster_id = os.getenv("NILLION_CLUSTER_ID")
    print(cluster_id)
    grpc_endpoint = os.getenv("NILLION_NILCHAIN_GRPC")
    chain_id = os.getenv("NILLION_NILCHAIN_CHAIN_ID")
    seed = "party_3_seed"
    client_Party_3 = create_nillion_client(
        UserKey.from_seed(seed),
        NodeKey.from_seed(seed),
    )

    my_program_name = "main"

    # Note: check out the code for the full millionaires program in the nada_programs folder
    program_mir_path = f"/content/nillion-python-starter/quickstart/nada_quickstart_programs/target/{my_program_name}.nada.bin"
    print(program_mir_path)
    payments_config = create_payments_config(chain_id, grpc_endpoint)
    payments_client = LedgerClient(payments_config)
    payments_wallet = LocalWallet(
        PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
        prefix="nillion",
    )

    # Pay to store the program
    receipt_store_program = await get_quote_and_pay(
        client_Party_3,
        nillion.Operation.store_program(program_mir_path),
        payments_wallet,
        payments_client,
        cluster_id,
    )

    # Store millionaires program in the network
    print(f"Storing program in the network: {my_program_name}")
    program_id = await client_Party_3.store_program(
        cluster_id, my_program_name, program_mir_path, receipt_store_program
    )

    # Set permissions for the client to compute on the program
    permissions = nillion.Permissions.default_for_user(client_Party_3.user_id)
    permissions.add_compute_permissions({client_Party_3.user_id: {program_id}})

    user_id_party_3 = client_Party_3.user_id
    program_id = f"{user_id_party_3}/{my_program_name}"

    print(f"Party_3 stores millionaires program at program_id: {program_id}")
    print(f"Party_3 tells Party_1 and Party_2 its user_id and the my program_id")

    # start a list of store ids to keep track of stored secrets
    store_ids = []
    party_ids = []

    for party_info in CONFIG_N_PARTIES:
        party_seed = party_info["party_name"] + "_seed"
        client_n = create_nillion_client(
            UserKey.from_seed(party_seed),
            NodeKey.from_seed(party_seed),
        )
        party_id_n = client_n.party_id
        user_id_n = client_n.user_id

        payments_config_n = create_payments_config(chain_id, grpc_endpoint)
        payments_client_n = LedgerClient(payments_config_n)
        payments_wallet_n = LocalWallet(
            PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
            prefix="nillion",
        )

        party_name = party_info["party_name"]
        secret_name = party_info["secret_name"]
        secret_value = party_info["secret_value"]

        # Create a secret for the current party
        stored_secret = nillion.NadaValues(
            {secret_name: nillion.SecretInteger(secret_value)}
        )

        # Create permissions object with default permissions for the current user
        permissions = nillion.Permissions.default_for_user(user_id_n)

        # Give compute permissions to Alice so she can use the secret in the specific millionionaires program by program id
        compute_permissions = {
            user_id_party_3: {program_id},
        }
        permissions.add_compute_permissions(compute_permissions)
        print(
            f"\n👍 {party_name} gives compute permissions on their secret to Alice's user_id: {user_id_party_3}"
        )

        receipt_store = await get_quote_and_pay(
            client_n,
            nillion.Operation.store_values(stored_secret, ttl_days=5),
            payments_wallet_n,
            payments_client_n,
            cluster_id,
        )
        # Store the permissioned secret
        store_id = await client_n.store_values(
            cluster_id, stored_secret, permissions, receipt_store
        )

        store_ids.append(store_id)
        party_ids.append(party_id_n)

        print(
            f"\n🎉 {party_name} stored {secret_name}: {secret_value} at store id: {store_id}"
        )

    party_ids_to_store_ids = " ".join(
        [f"{party_id}:{store_id}" for party_id, store_id in zip(party_ids, store_ids)]
    )

    # print(party_ids_to_store_ids)

    # Alice initializes a client
    # client_Party_3 = create_nillion_client(
    #     UserKey.from_seed(seed),
    #     NodeKey.from_seed(seed),
    # )
    party_id_party_3 = client_Party_3.party_id

    payments_config = create_payments_config(chain_id, grpc_endpoint)
    payments_client = LedgerClient(payments_config)
    payments_wallet = LocalWallet(
        PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
        prefix="nillion",
    )

    # Create computation bindings for millionaires program
    compute_bindings = nillion.ProgramBindings(program_id)

    # Add Alice as an input party
    # compute_bindings.add_input_party(CONFIG_PARTY_1["party_name"], party_id_party_3)

    # Add an output party (Alice).
    # The output party reads the result of the blind computation
    compute_bindings.add_output_party(CONFIG_PARTY_1["party_name"], party_id_party_3)

    print(f"Computing using program {program_id}")

    # Also add Bob and Charlie as input parties
    party_ids_to_store_ids_1 = {}
    i = 0
    for party_id, store_id in zip(party_ids, store_ids):
        # party_id, store_id = pair.split(":")
        party_name = CONFIG_N_PARTIES[i]["party_name"]
        compute_bindings.add_input_party(party_name, party_id)
        party_ids_to_store_ids_1[party_id] = store_id
        i = i + 1

    # Add any computation time secrets
    # Alice provides her salary at compute time
    # party_name = CONFIG_PARTY_1["party_name"]
    # secret_name = CONFIG_PARTY_1["secret_name"]
    # secret_value_alice = CONFIG_PARTY_1["secret_value"]
    compute_time_secrets = nillion.NadaValues({})

    # Pay for the compute
    receipt_compute = await get_quote_and_pay(
        client_Party_3,
        nillion.Operation.compute(program_id, compute_time_secrets),
        payments_wallet,
        payments_client,
        cluster_id,
    )

    # print(
    #     f"\n🎉 {party_name} provided {secret_name}: {secret_value_alice} as a compute time secret"
    # )

    # Compute on the secret with all store ids. Note that there are no compute time secrets or public variables
    compute_id = await client_Party_3.compute(
        cluster_id,
        compute_bindings,
        list(party_ids_to_store_ids_1.values()),  # Bob and Charlie's stored secrets
        compute_time_secrets,  # Alice's computation time secret
        receipt_compute,
    )


    print(f"The computation was sent to the network. compute_id: {compute_id}")
    while True:
        compute_event = await client_Party_3.next_compute_event()
        if isinstance(compute_event, nillion.ComputeFinishedEvent):
            print(f"✅  Compute complete for compute_id {compute_event.uuid}")
            if (compute_event.result.value['result_1']==0):
              print(f"🖥️  The GDC of two secrect is {compute_event.result.value['result_0']}")
              return compute_event.result.value['result_0']
            else:

                # Create a secret for the current party
                stored_secret_result_0 = nillion.NadaValues(
                    {secret_name: nillion.SecretInteger(compute_event.result.value['result_0'])}
                )

                stored_secret_result_1 = nillion.NadaValues(
                    {secret_name: nillion.SecretInteger(compute_event.result.value['result_1'])}
                )

                permissions = nillion.Permissions.default_for_user(user_id_party_3)

                # Give compute permissions to Alice so she can use the secret in the specific millionionaires program by program id
                compute_permissions = {
                    user_id_party_3: {program_id},
                }
                permissions.add_compute_permissions(compute_permissions)

                receipt_store_result_0 = await get_quote_and_pay(
                    client_n,
                    nillion.Operation.store_values(stored_secret_result_0, ttl_days=5),
                    payments_wallet_n,
                    payments_client_n,
                    cluster_id,
                )

                receipt_store_result_1 = await get_quote_and_pay(
                    client_n,
                    nillion.Operation.store_values(stored_secret_result_1, ttl_days=5),
                    payments_wallet_n,
                    payments_client_n,
                    cluster_id,
                )
                # Store the permissioned secret
                store_id_result_0 = await client_n.store_values(
                    cluster_id, stored_secret_result_0, permissions, receipt_store_result_0
                )

                store_id_result_0 = await client_n.store_values(
                    cluster_id, stored_secret_result_1, permissions, receipt_store_result_1
                )
                
                compute_id = await client_Party_3.compute(cluster_id,
                  compute_bindings,
                  list(store_id_result_0,stored_secret_result_1),  # Bob and Charlie's stored secrets
                  compute_time_secrets,  # Alice's computation time secret
                  receipt_compute,
              )

            print(f"🖥️  The result is {compute_event.result.value}")
            # return compute_event.result.value

if __name__ == "__main__":
    asyncio.run(main())