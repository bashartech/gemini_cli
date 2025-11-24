from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from models import User, Transfer, UserUpdate, UserIdentifier
from database import users

app = FastAPI()

@app.post("/authenticate")
def authenticate(user: User):
    """
    Authenticates a user and returns their balance.
    """
    if user.name in users and users[user.name]["pin"] == user.pin:
        return {"message": f"Welcome, {user.name}!", "balance": users[user.name]["balance"]}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid name or PIN",
        )

@app.post("/banktransfer")
def bank_transfer(transfer: Transfer):
    """
    Transfers an amount from a sender to a recipient.
    """
    sender = users.get(transfer.sender_name)
    recipient = users.get(transfer.recipient_name)

    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sender not found",
        )

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found",
        )

    if sender["balance"] < transfer.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds",
        )

    # Perform the transfer
    sender["balance"] -= transfer.amount
    recipient["balance"] += transfer.amount

    # Redirect to the authenticate page with the recipient's name
    return RedirectResponse(
        url=f"/authenticate?name={transfer.recipient_name}",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@app.get("/authenticate")
def get_authenticate(name: str):
    """
    A GET endpoint for the authenticate page to show the balance after transfer.
    This would typically be a rendered HTML page in a real application.
    """
    if name in users:
        return {
            "message": f"Authentication required for {name}. Please provide your PIN to see your balance.",
            "name": name,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

@app.put("/user/{name}", status_code=status.HTTP_200_OK)
def create_or_update_user(name: str, update_data: UserUpdate):
    """
    Creates a new user or updates an existing user's balance.
    - If the user exists, the provided PIN must match to update the balance.
    - If the user does not exist, a new user is created with the provided details.
    """
    if name in users:
        # Update existing user
        if users[name]["pin"] == update_data.pin:
            users[name]["balance"] = update_data.balance
            return {"message": f"User {name}'s balance updated successfully.", "balance": users[name]["balance"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid PIN for user update",
            )
    else:
        # Create new user
        users[name] = {"pin": update_data.pin, "balance": update_data.balance}
        return {"message": f"User {name} created successfully.", "user_details": users[name]}, status.HTTP_201_CREATED

@app.delete("/user/{name}")
def delete_user(name: str, user_identifier: UserIdentifier):
    """
    Deletes a user if the provided PIN is correct.
    """
    if name not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if users[name]["pin"] == user_identifier.pin:
        del users[name]
        return {"message": f"User {name} deleted successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN for user deletion",
        )
