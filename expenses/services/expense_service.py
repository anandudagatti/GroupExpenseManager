from django.db import transaction

from .split_calculator import SplitCalculator


class ExpenseService:
    """
    Handles expense creation and related business logic.
    """

    @staticmethod
    @transaction.atomic
    def create_expense(
        *,
        user,
        group,
        amount,
        date,
        category,
        description,
        participants
    ):
        """
        participants format:
        [
            {"user": user_obj, "ratio": 50},
            {"user": user_obj, "ratio": 50},
        ]
        """

        # NOTE:
        # Actual model imports and save logic
        # will be added in the NEXT step.
        # This is a safe placeholder.

        splits = SplitCalculator.calculate(amount, participants)

        return {
            "splits": splits
        }
