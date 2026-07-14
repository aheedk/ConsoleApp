"""
Simple Banking System - Console App

Features:
    - Create an account
    - View account details
    - Deposit money
    - Withdraw money
    - View transaction history

This is organized using MVC so the same logic could later grow into a
real web app
"""


import re       # regex module - used to check the email format
import random   # used to generate random account numbers


# MODEL - data and business rules
# In a real app these would map to database tables. Each Account is one row in
# an `accounts` table; each Transaction is one row in a `transactions` table.


class Transaction:
    """One record of money moving in or out. Maps to a row in `transactions`."""

    def __init__(self, kind, amount):
        self.kind = kind        # "deposit" or "withdraw"
        self.amount = amount


class Account:
    """A single bank account. Maps to a row in an `accounts` table."""

    def __init__(self, account_id, owner, email):
        # Business rule: reject an invalid email before the account even exists.
        if not is_valid_email(email):
            raise ValueError("Invalid email address")
        self.account_id = account_id    # would be the PRIMARY KEY in SQL
        self.owner = owner
        self.email = email
        self.balance = 0
        self.transactions = []          # would be a linked `transactions` table

    def deposit(self, amount):
        # Business rule: deposits must be positive.
        if amount <= 0:
            raise ValueError("Deposit must be greater than 0")
        self.balance += amount
        self.transactions.append(Transaction("deposit", amount))

    def withdraw(self, amount):
        # Business rules: positive amount, and you can't overdraw.
        if amount <= 0:
            raise ValueError("Withdrawal must be greater than 0")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.transactions.append(Transaction("withdraw", amount))


class Bank:
    """
    Holds all accounts. This is our 'database' for now - just an in-memory dict.
    Swapping this dict for real SQL queries is the only change needed later.
    """

    def __init__(self):
        self._accounts = {}     # { account_id: Account }

    def _generate_account_number(self):
        # Roll a random 8-digit number. If it's already taken, roll again.
        # The loop guarantees the number we return is NOT already in use.
        while True:
            number = random.randint(10_000_000, 99_999_999)
            if number not in self._accounts:
                return number

    def create_account(self, owner, email):
        account_id = self._generate_account_number()
        account = Account(account_id, owner, email)
        self._accounts[account_id] = account
        return account

    def get_account(self, account_id):
        # Like: SELECT * FROM accounts WHERE account_id = ?
        return self._accounts.get(account_id)


# VIEW - everything the user sees or types
# Later, a web frontend replaces these functions. Keeping all print/input here
# means the model and controller never deal with the user directly.

def show_menu():
    print("\n===== BANK MENU =====")
    print("1. Create account")
    print("2. View account details")
    print("3. Deposit")
    print("4. Withdraw")
    print("5. View transaction history")
    print("0. Exit")


def show_account(account):
    print(f"\nAccount #{account.account_id}")
    print(f"Owner:   {account.owner}")
    print(f"Email:   {account.email}")
    print(f"Balance: ${account.balance}")


def show_transactions(account):
    if not account.transactions:
        print("No transactions yet.")
        return
    print(f"\nTransaction history for account #{account.account_id}:")
    for t in account.transactions:
        print(f"  {t.kind:8} ${t.amount}")


def ask(prompt):
    return input(prompt).strip()


# =============================================================================
# CONTROLLER - reacts to user choices, connects View <-> Model
# =============================================================================
# Each function here is like one REST endpoint. For example, handle_deposit()
# is the console version of: POST /accounts/{id}/deposit

def handle_create(bank):
    owner = ask("Enter account owner name: ")

    # Keep asking until they type a real-looking email (no gibberish).
    while True:
        email = ask("Enter email: ")
        if is_valid_email(email):
            break
        print("That doesn't look like a valid email. Try again (e.g. name@example.com).")

    account = bank.create_account(owner, email)
    print(f"Created account #{account.account_id} for {owner} ({email})")

def handle_view(bank):
    account = find_account(bank)
    if account:
        show_account(account)


def handle_deposit(bank):
    account = find_account(bank)
    if not account:
        return
    try:
        amount = int(ask("Amount to deposit: "))
        account.deposit(amount)
        print(f"Deposited ${amount}. New balance: ${account.balance}")
    except ValueError as e:
        print(f"Error: {e}")


def handle_withdraw(bank):
    account = find_account(bank)
    if not account:
        return
    try:
        amount = int(ask("Amount to withdraw: "))
        account.withdraw(amount)
        print(f"Withdrew ${amount}. New balance: ${account.balance}")
    except ValueError as e:
        print(f"Error: {e}")


def handle_history(bank):
    account = find_account(bank)
    if account:
        show_transactions(account)


def find_account(bank):
    """Helper: ask for an id and look it up, or report if it's missing."""
    try:
        account_id = int(ask("Enter account number: "))
    except ValueError:
        print("Account number must be a whole number.")
        return None
    account = bank.get_account(account_id)
    if account is None:
        print("No account with that number.")
    return account

def is_valid_email(email):
    # A basic email rule: some text, an @, some text, a dot, some text,
    # and NO spaces anywhere. This rejects gibberish like "asdf" or "a b@c".
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None

# MAIN LOOP - starts the app and routes menu choices to the controller

def main():
    bank = Bank()
    print("Welcome to the Simple Bank!")

    while True:
        show_menu()
        choice = ask("Choose an option: ")

        if choice == "1":
            handle_create(bank)
        elif choice == "2":
            handle_view(bank)
        elif choice == "3":
            handle_deposit(bank)
        elif choice == "4":
            handle_withdraw(bank)
        elif choice == "5":
            handle_history(bank)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    main()
