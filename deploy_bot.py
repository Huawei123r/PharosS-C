import os
import time
import random
import json
from web3 import Web3
#from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
from solcx import compile_standard, install_solc
from decimal import Decimal
from eth_account import Account # For generating random wallets

# --- Configuration ---
load_dotenv()

WEB3_PROVIDER_URL = os.getenv("WEB3_PROVIDER_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# --- Constants ---
INITIAL_DELAY_HOURS = 24
MIN_RANDOM_INTERVAL_HOURS = 1
MAX_RANDOM_INTERVAL_HOURS = 6

CONTRACTS_DIR = "contracts"
GAS_LIMIT = 3_000_000 # Increased gas limit for more complex transactions
DEFAULT_TOKEN_TRANSFER_COUNT = 3 # How many transfers per deployed token contract

# --- Random Word List (for token names/symbols) ---
COMMON_WORDS = [
    "Alpha", "Beta", "Gamma", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliett",
    "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo", "Sierra", "Tango",
    "Uniform", "Victor", "Whiskey", "Xray", "Yankee", "Zulu", "Spark", "Nexus", "Quantum", "Hyper",
    "Astro", "Nova", "Flux", "Core", "Zenith", "Pinnacle", "Vortex", "Mirage", "Apex", "Horizon"
]

# --- Web3 Setup ---
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))

# For PoA chains like Sepolia, Goerli, you might need this middleware
# Check chain ID: Sepolia (11155111), Goerli (5), Mainnet (1)
#if w3.eth.chain_id in [11155111, 5]: # Replace with Pharos Testnet ID if different and it's PoA
 #   w3.middleware_onion.inject(geth_poa_middleware, layer=0)


if not w3.is_connected():
    print("Failed to connect to Ethereum node. Check WEB3_PROVIDER_URL in .env")
    exit()

print(f"Connected to Ethereum network: Chain ID {w3.eth.chain_id}")

# --- Account Setup ---
try:
   
    account = Account.from_key(PRIVATE_KEY)
    w3.eth.default_account = account.address
    print(f"Deployment account: {account.address}")
    balance_wei = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance_wei, 'ether')
    print(f"Account balance: {balance_eth:.4f} ETH")
    if balance_eth < 0.001:
        print("WARNING: Low test ETH balance. Deployment might fail due to insufficient gas.")
except Exception as e:
    print(f"Error setting up account or getting balance: {e}")
    print("Please check your PRIVATE_KEY in .env and ensure it's correct and funded on the testnet.")
    exit()

# --- Helper Functions ---
def generate_random_word_phrase(count=1):
    """Generates a phrase from random words."""
    return " ".join(random.choices(COMMON_WORDS, k=count))

def generate_random_ethereum_address():
    """Generates a new random Ethereum address (just the address, no private key stored)."""
    return Account.create().address

# --- Contract Compilation Function ---
def compile_contract(contract_name: str, sol_code: str):
    """Compiles a single Solidity contract."""
    print(f"Compiling {contract_name}...")
    try:
        install_solc() # Ensure solc compiler is installed
        compiled_sol = compile_standard(
            {
                "language": "Solidity",
                "sources": {contract_name: {"content": sol_code}},
                "settings": {
                    "outputSelection": {
                        "*": {
                            "*": ["abi", "evm.bytecode"]
                        }
                    },
                    "optimizer": {
                        "enabled": True,
                        "runs": 200
                    }
                },
            },
            solc_version="0.8.0",
        )
        contract_key = contract_name.split('.')[0]
        contract_data = compiled_sol["contracts"][contract_name][contract_key]
        bytecode = contract_data["evm"]["bytecode"]["object"]
        abi = contract_data["abi"]
        print(f"{contract_name} compiled successfully.")
        return {"bytecode": bytecode, "abi": abi}
    except Exception as e:
        print(f"Error compiling {contract_name}: {e}")
        return None

# --- Deployment Function ---
def deploy_contract(compiled_contract: dict, value_wei: int = 0, *constructor_args):
    """
    Deploys a compiled smart contract.
    Args:
        compiled_contract: Dictionary containing 'bytecode' and 'abi'.
        value_wei: Amount of WEI to send with the contract creation (for payable constructors).
        constructor_args: Arguments for the contract's constructor.
    Returns:
        (contract_address: str, contract_instance: web3.contract.Contract) if successful, else (None, None)
    """
    try:
        contract_bytecode = compiled_contract["bytecode"]
        contract_abi = compiled_contract["abi"]

        Contract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

        tx_params = {
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': GAS_LIMIT,
            'gasPrice': w3.eth.gas_price,
            'value': value_wei
        }

        if constructor_args:
            transaction = Contract.constructor(*constructor_args).build_transaction(tx_params)
        else:
            transaction = Contract.constructor().build_transaction(tx_params)

        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
        print("Sending deployment transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Transaction sent. TX Hash: {tx_hash.hex()}")

        print("Waiting for transaction receipt (up to 10 minutes)...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
        print("Transaction confirmed!")

        if tx_receipt.status == 1:
            contract_address = tx_receipt.contractAddress
            deployed_contract_instance = w3.eth.contract(address=contract_address, abi=contract_abi)
            print(f"Contract successfully deployed to: {contract_address}")
            return contract_address, deployed_contract_instance
        else:
            print(f"Transaction failed. Status: {tx_receipt.status}. Check gas, nonce, or contract code.")
            return None, None

    except Exception as e:
        print(f"Error during contract deployment: {e}")
        try:
            print(f"Current nonce for {account.address}: {w3.eth.get_transaction_count(account.address)}")
        except Exception:
            pass
        return None, None

# --- Transaction Helper Function ---
def send_transaction(contract_instance, function_name, *args, value_wei: int = 0):
    """
    Helper to send a transaction to a deployed contract (e.g., transfer, mint).
    """
    try:
        func = getattr(contract_instance.functions, function_name)
        tx_params = {
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': GAS_LIMIT, # Using the general GAS_LIMIT for simplicity
            'gasPrice': w3.eth.gas_price,
            'value': value_wei
        }

        # Estimate gas before building transaction to catch issues early
        try:
            # Need to build and estimate to ensure correct gas estimation
            estimated_gas = func(*args).estimate_gas(tx_params)
            tx_params['gas'] = estimated_gas + 50000 # Add a buffer
        except Exception as e:
            print(f"Warning: Could not estimate gas for {function_name}. Using default GAS_LIMIT. Error: {e}")


        transaction = func(*args).build_transaction(tx_params)
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)

        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"  Sending {function_name} transaction. TX Hash: {tx_hash.hex()}")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300) # 5 min timeout

        if tx_receipt.status == 1:
            print(f"  {function_name} transaction confirmed!")
            return True
        else:
            print(f"  {function_name} transaction failed. Status: {tx_receipt.status}.")
            return False
    except Exception as e:
        print(f"  Error sending {function_name} transaction: {e}")
        return False

# --- Main Bot Logic ---
def main():
    try:
        print("Ensuring solc compiler is installed...")
        install_solc()
        print("Solc compiler ready.")
    except Exception as e:
        print(f"Warning: Could not install solc automatically. Please install it manually if compilation fails: {e}")

    print(f"Initial wait for {INITIAL_DELAY_HOURS} hours before first deployment...")
    time.sleep(INITIAL_DELAY_HOURS * 3600)
    print("Initial delay complete. Starting deployment cycle.")

    while True:
        try:
            contract_files = [f for f in os.listdir(CONTRACTS_DIR) if f.endswith(".sol")]
            if not contract_files:
                print(f"No Solidity files found in {CONTRACTS_DIR}. Please add some.")
                time.sleep(60)
                continue

            selected_contract_file = random.choice(contract_files)
            contract_path = os.path.join(CONTRACTS_DIR, selected_contract_file)

            with open(contract_path, 'r') as f:
                sol_code = f.read()

            print(f"\n--- Deploying {selected_contract_file} ---")

            constructor_args = []
            eth_value_for_deployment_wei = 0
            deployed_contract_instance = None # To hold the instance for post-deployment actions

            if "Greeter.sol" in selected_contract_file:
                greetings = ["Hello from Bot!", "Greetings!", "Test deployment!", "Random deploy!", "GM!"]
                constructor_args = [random.choice(greetings)]
                print(f"Greeter constructor arg: '{constructor_args[0]}'")
            elif "SimpleTimeLock.sol" in selected_contract_file:
                lock_duration_seconds = random.randint(60, 300) # 1 to 5 minutes
                eth_to_lock = Decimal(str(random.uniform(0.0001, 0.0005)))
                
                constructor_args = [lock_duration_seconds]
                eth_value_for_deployment_wei = w3.to_wei(eth_to_lock, 'ether')
                
                print(f"SimpleTimeLock constructor arg: {lock_duration_seconds} seconds")
                print(f"Amount of ETH to lock: {eth_to_lock:.5f} ETH")

                estimated_total_cost_eth = eth_to_lock + w3.from_wei(GAS_LIMIT * w3.eth.gas_price, 'ether')
                if w3.from_wei(w3.eth.get_balance(account.address), 'ether') < estimated_total_cost_eth:
                    print(f"ERROR: Insufficient funds for SimpleTimeLock deployment. Need approx {estimated_total_cost_eth:.5f} ETH.")
                    print("Skipping this deployment and waiting for next interval.")
                    time.sleep(60)
                    continue
            elif "EventEmitter.sol" in selected_contract_file:
                print("EventEmitter has no specific constructor arguments.")
                constructor_args = []
            elif "Owned.sol" in selected_contract_file:
                print("Owned contract's owner is set to the deployer.")
                constructor_args = []
            elif "EtherVault.sol" in selected_contract_file:
                print("EtherVault contract deployed. It can receive and hold Ether.")
                constructor_args = []
            elif "ERC20Random.sol" in selected_contract_file:
                token_name = generate_random_word_phrase(2) + " Token"
                token_symbol = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=random.randint(3, 5)))
                initial_supply = random.randint(1000, 100000) # Random supply
                
                constructor_args = [token_name, token_symbol, initial_supply]
                print(f"ERC20 Token: Name='{token_name}', Symbol='{token_symbol}', Supply={initial_supply}")

            elif "ERC721Random.sol" in selected_contract_file:
                nft_name = generate_random_word_phrase(2) + " NFT"
                nft_symbol = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=random.randint(3, 5))) + "NFT"
                
                constructor_args = [nft_name, nft_symbol]
                print(f"ERC721 NFT: Name='{nft_name}', Symbol='{nft_symbol}'")
                
            else:
                print(f"Warning: Unknown contract '{selected_contract_file}'. Assuming no constructor arguments and no ETH value.")

            compiled_contract = compile_contract(selected_contract_file, sol_code)
            if compiled_contract:
                deploy_address, deployed_contract_instance = deploy_contract(
                    compiled_contract, eth_value_for_deployment_wei, *constructor_args
                )
                if deploy_address:
                    print(f"Successfully deployed {selected_contract_file} to {deploy_address}")

                    # --- Post-Deployment Token Operations ---
                    if "ERC20Random.sol" in selected_contract_file and deployed_contract_instance:
                        print(f"Performing {DEFAULT_TOKEN_TRANSFER_COUNT} ERC20 transfers...")
                        erc20_decimals = deployed_contract_instance.functions.decimals().call()
                        for i in range(DEFAULT_TOKEN_TRANSFER_COUNT):
                            recipient = generate_random_ethereum_address()
                            transfer_amount_raw = random.randint(1, 10) * (10**erc20_decimals) # Transfer 1-10 tokens
                            
                            # Check if the deployer account has enough of the new ERC20 tokens
                            current_token_balance = deployed_contract_instance.functions.balanceOf(account.address).call()
                            if current_token_balance < transfer_amount_raw:
                                print(f"  Insufficient ERC20 token balance ({current_token_balance}) to transfer {transfer_amount_raw}. Skipping transfers.")
                                break # Stop transfers if balance is too low

                            print(f"  Transferring {w3.from_wei(transfer_amount_raw, 'ether')} {deployed_contract_instance.functions.symbol().call()} to {recipient}...")
                            send_transaction(deployed_contract_instance, "transfer", recipient, transfer_amount_raw)
                            time.sleep(random.uniform(5, 15)) # Small delay between transfers

                    elif "ERC721Random.sol" in selected_contract_file and deployed_contract_instance:
                        print(f"Minting and transferring {DEFAULT_TOKEN_TRANSFER_COUNT} ERC721 NFTs...")
                        # Mint NFTs to the deployer first
                        minted_token_ids = []
                        for i in range(DEFAULT_TOKEN_TRANSFER_COUNT):
                            print(f"  Minting NFT {i+1} to {account.address}...")
                            # Assuming mint function exists and is callable by owner
                            mint_success = send_transaction(deployed_contract_instance, "mint", account.address)
                            if mint_success:
                                # Retrieve the newly minted token ID (requires parsing events or a counter)
                                # For this simplified contract, let's assume `_tokenIdCounter` is the new ID.
                                # In a real scenario, you'd parse Transfer events or check the counter after each mint.
                                try:
                                    last_token_id = deployed_contract_instance.functions._tokenIdCounter().call() # Assuming this is public
                                    minted_token_ids.append(last_token_id)
                                except Exception:
                                    print("Could not retrieve new token ID via _tokenIdCounter(). Skipping transfer for this NFT.")
                                    # Fallback: if we can't get the ID, we can't transfer it reliably.
                                    pass
                            time.sleep(random.uniform(5, 15)) # Small delay after mint

                        # Transfer minted NFTs to random wallets
                        for token_id in minted_token_ids:
                            recipient = generate_random_ethereum_address()
                            print(f"  Transferring NFT ID {token_id} from {account.address} to {recipient}...")
                            # safeTransferFrom(address from, address to, uint tokenId)
                            send_transaction(deployed_contract_instance, "safeTransferFrom", account.address, recipient, token_id)
                            time.sleep(random.uniform(5, 15)) # Small delay between transfers

                else:
                    print(f"Failed to deploy {selected_contract_file}.")
            else:
                print(f"Skipping deployment of {selected_contract_file} due to compilation error.")

            random_interval_seconds = random.uniform(MIN_RANDOM_INTERVAL_HOURS, MAX_RANDOM_INTERVAL_HOURS) * 3600
            print(f"Next deployment in approximately {random_interval_seconds / 3600:.2f} hours...")
            time.sleep(random_interval_seconds)

        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            print("Retrying in 5 minutes...")
            time.sleep(300)

if __name__ == "__main__":
    main()
