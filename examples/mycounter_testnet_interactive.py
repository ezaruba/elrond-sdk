import base64
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

    # We initialize the smart contract with an actual address if IF was previously deployed,
    # so that we can start to interact with it ("query_flow")
    contract = SmartContract(address=args.contract)

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

    def execute_flow(function):
        global contract

        tx = environment.execute_contract(contract, caller=bob, function=function)
        logger.info("Tx hash: %s", tx)

    while True:
        print("Let's run a flow.")
        print("1. Deploy smart contract")
        print("2. Query smart contract")
        print("3. Call smart contract: increment")
        print("4. Call smart contract: decrement")

        try:
            choice = int(input("Choose:\n"))
        except Exception:
            break

        if choice == 1:
            environment.run_flow(deploy_flow)
        elif choice == 2:
            environment.run_flow(query_flow)
        elif choice == 3:
            environment.run_flow(lambda: execute_flow("increment"))
        elif choice == 4:
            environment.run_flow(lambda: execute_flow("decrement"))
