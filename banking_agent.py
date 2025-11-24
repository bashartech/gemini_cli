import os, asyncio
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Tool, function_tool, Runner, SQLiteSession
from database import users # Import users from database.py
from dotenv import load_dotenv

load_dotenv()
# --- Step 2: Define the Functionality as Python Functions ---
# Each function replicates the logic from your FastAPI endpoints.
@function_tool()
def authenticate_user(name: str, pin) -> str:
    """
    Authenticates a user with their name and PIN to securely check their account balance.
    Returns a welcome message with the balance on success, or an error message on failure.
    """

    print(f"TOOL: Authenticating user '{name}'...")
    if name in users and users[name]["pin"] == pin:
        return f"Authentication successful. Welcome, {name}! Your current balance is ${users[name]['balance']}."
    else:
        return "Authentication failed. The provided name or PIN is incorrect."
@function_tool()
def transfer_funds(sender_name: str, recipient_name: str, amount: float) -> str:
    """
    Transfers a specific amount of money from a sender's account to a recipient's account.
    The sender must exist, the recipient must exist, and the sender must have sufficient funds.
    """
    print(f"TOOL: Transferring ${amount} from '{sender_name}' to '{recipient_name}'...")
    if sender_name not in users:
        return f"Error: Sender '{sender_name}' not found."
    if recipient_name not in users:
        return f"Error: Recipient '{recipient_name}' not found."
    if users[sender_name]["balance"] < amount:
        return f"Error: Insufficient funds. {sender_name} has only ${users[sender_name]['balance']}."

    # Perform the transfer
    users[sender_name]["balance"] -= amount
    users[recipient_name]["balance"] += amount
    return f"Success! Transferred ${amount} to {recipient_name}. {sender_name}'s new balance is ${users[sender_name]['balance']}."

@function_tool()
def create_or_update_user(name: str, pin, balance: float) -> str:
    """
    Creates a new user account or updates an existing user's balance.
    If the user exists, this tool updates their balance. A PIN is required for creation but not for the update itself in this simulation.
    If the user does not exist, a new ac
    count is created with the provided details.
    """
    pin = str(pin)
    print(f"TOOL: Creating or updating user '{name}'...")
    if name in users:
        users[name]["balance"] = balance
        return f"Successfully updated balance for user '{name}'. New balance is ${balance}."
    else:
        users[name] = {"pin": pin, "balance": balance}
        return f"Successfully created new user '{name}' with a balance of ${balance}."

@function_tool()
def delete_user(name: str, pin) -> str:
    """
    Permanently deletes a user's account from the bank.
    This is an irreversible action that requires the user's name and correct PIN for authorization.
    """
    pin = str(pin)
    print(f"TOOL: Deleting user '{name}'...")
    if name not in users:
        return f"Error: User '{name}' not found."
    if users[name]["pin"] != pin:
        return "Error: Invalid PIN. Deletion unauthorized."

    del users[name]
    return f"Success! User '{name}' has been permanently deleted."

# --- Step 3: Setup the Model and Client ---
try:
    api_key = os.getenv("GEMINI_API_KEY")
except KeyError:
    print("ERROR: The GEMINI_API_KEY environment variable is not set.")
    exit()

# The OpenAI SDK client is configured to point to Gemini's API endpoint
client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta",
)

# The model wrapper from the agent-sdk
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# --- Step 4: Create the Agent with Tools and Instructions ---
instructions = """
You are a highly capable and trustworthy banking assistant. Your primary role is to help users manage their bank accounts by interacting with a secure banking API on their behalf.

You must operate under the following principles:
1.  **Clarity and Confirmation**: Always be clear about the action you are about to perform. For sensitive operations like transferring funds or deleting users, explicitly ask for confirmation before proceeding.
2.  **Information Gathering**: You must gather all necessary information from the user before using a tool. For example, to transfer funds, you need the sender's name, the recipient's name, and the amount. Do not attempt to use a tool with incomplete information.
3.  **Tool-Based Actions**: Your ONLY method of interacting with the bank is through the provided functions (tools). Do not make up balances or transaction statuses.
4.  **Security First**: Never ask for more information than a tool requires. Handle user data like names and PINs with care.
"""

# Initialize the agent
banking_agent = Agent(
    model=model,
    tools=[delete_user, create_or_update_user, transfer_funds, authenticate_user ],
    instructions=instructions,
    name="BankingAgent"
)

# --- Step 5: Run the Agent in an Interactive Loop ---
print("Banking Agent is now active. Type 'exit' to end the session.")
print("---------------------------------------------------------")

async def main():
 session = SQLiteSession("bankingSession123")
 while True:
    user_input = input("You: ")
    if user_input.lower() == 'exit':
        print("Ending session. Goodbye!")
        break
    
    # The agent processes the input, decides whether to call a tool, and generates a response
    response = await Runner.run( 
        starting_agent= banking_agent,
        input=user_input,
        session=session
        ) 
    print(f"Agent: {response.final_output}")

asyncio.run(main())