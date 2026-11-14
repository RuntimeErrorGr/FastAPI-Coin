from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

Money = Annotated[
    Decimal,
    PlainSerializer(lambda value: format(value, "f"), return_type=str),
]
"""A Decimal amount, sent to clients as a plain string such as "0.50000000"."""
