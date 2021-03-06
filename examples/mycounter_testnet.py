import base64
import time
import logging
from argparse import ArgumentParser

from erdpy.accounts import Account
from erdpy.contracts import SmartContract
from erdpy.environments import TestnetEnvironment
from erdpy.projects import ProjectClang

logger = logging.getLogger("examples")


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--proxy", help="Testnet Proxy URL", required=True)
    parser.add_argument("--contract", help="Existing contract address", default="0000000000000000050000000000000000000000000000000000000000000000")
    parser.add_argument("--pem", help="User PEM file", required=True)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    # First, create a sample project called "mycounter" based on the template "simple-counter" (written in C)
    # erdpy new --template simple-counter --directory ./examples hello

    # Create a project object afterwards
    project = ProjectClang("./examples/contracts/mycounter")

    # This will build the smart contract.
    # If the buildchain is missing, it will be installed automatically.
    project.build()

    # We can inspect the bytecode like this:
    bytecode = project.get_bytecode()
    logger.info("Bytecode: %s", bytecode)

    # Now, we create a environment which intermediates deployment and execution
    environment = TestnetEnvironment(args.proxy)
    bob = Account(pem_file=args.pem)

    contract = SmartContract()

    # A flow defines the desired steps to interact with the contract.
    def deploy_flow():
        global contract

        # For deploy, we initialize the smart contract with the compiled bytecode
        contract = SmartContract(bytecode=bytecode)
        tx, address = environment.deploy_contract(contract, owner=bob)
        logger.info("Tx hash: %s", tx)
        logger.info("Contract address (hex): %s", address.hex())
        logger.info("Contract address (bech32): %s", address.bech32())

    def query_flow():
        global contract

        answer = environment.query_contract(contract, "get")[0]
        answer_bytes = base64.b64decode(answer)
        answer_hex = answer_bytes.hex()
        answer_int = int(answer_hex, 16)
        logger.info(f"Answer: {answer_bytes}, {answer_hex}, {answer_int}")
        return answer_int

    def execute_flow(function):
        global contract

        tx = environment.execute_contract(contract, caller=bob, function=function)
        logger.info("Tx hash: %s", tx)

    def wait_a_bit():
        print("Wait 30 seconds")
        time.sleep(30)

    environment.run_flow(deploy_flow)
    wait_a_bit()
    value = environment.run_flow(query_flow)
    assert value == 0
    environment.run_flow(lambda: execute_flow("increment"))
    wait_a_bit()
    value = environment.run_flow(query_flow)
    assert value == 1
