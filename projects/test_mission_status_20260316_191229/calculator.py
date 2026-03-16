class Calculator:
    """
    Une classe simple pour effectuer des opérations arithmétiques de base.
    """

    def add(self, a: float | int, b: float | int) -> float | int:
        """Additionne deux nombres."""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValueError("Les deux entrées doivent être des nombres.")
        return a + b

    def subtract(self, a: float | int, b: float | int) -> float | int:
        """Soustrait le deuxième nombre du premier."""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValueError("Les deux entrées doivent être des nombres.")
        return a - b

    def multiply(self, a: float | int, b: float | int) -> float | int:
        """Multiplie deux nombres."""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValueError("Les deux entrées doivent être des nombres.")
        return a * b

    def divide(self, a: float | int, b: float | int) -> float:
        """Divise le premier nombre par le second."""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValueError("Les deux entrées doivent être des nombres.")
        if b == 0:
            raise ValueError("Division par zéro impossible.")
        return a / b