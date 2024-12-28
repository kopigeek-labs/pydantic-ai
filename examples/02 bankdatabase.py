"""Database connection module for handling customer banking operations."""

class DatabaseConn:
    """This is a fake database for example purposes.

    In reality, you'd be connecting to an external database
    (e.g. PostgreSQL) to get information about customers.
    """

    @classmethod
    async def customer_name(cls, *, customer_id: int) -> str | None:
        """Retrieve customer name by their ID.

        Args:
            customer_id: Customer's unique identifier

        Returns:
            str | None: Customer's name if found, None otherwise
        """
        if customer_id == 123:
            return 'John'

    @classmethod
    async def customer_balance(cls, *, customer_id: int, include_pending: bool) -> float:
        """Get customer's account balance.

        Args:
            customer_id: Customer's unique identifier
            include_pending: Whether to include pending transactions

        Returns:
            float: Current balance amount

        Raises:
            ValueError: If customer is not found
        """
        if customer_id == 123:
            balance = 123.45
            pending = 10.00 if include_pending else 0.00
            return balance + pending
        else:
            raise ValueError('Customer not found')
