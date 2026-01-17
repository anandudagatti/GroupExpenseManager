from decimal import Decimal, ROUND_HALF_UP


class SplitCalculator:
    """
    Central authority for expense split calculations.
    """

    @staticmethod
    def calculate(amount, participants):
        """
        amount: Decimal
        participants: list of dicts
            [
                {"user": user_obj, "ratio": 50},
                {"user": user_obj, "ratio": 50},
            ]
        """

        if not participants:
            raise ValueError("Participants list cannot be empty")

        total_ratio = sum(p["ratio"] for p in participants)

        if total_ratio <= 0:
            raise ValueError("Total ratio must be greater than zero")

        splits = {}

        for p in participants:
            share = (Decimal(amount) * Decimal(p["ratio"]) / Decimal(total_ratio))
            splits[p["user"]] = share.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        return splits
