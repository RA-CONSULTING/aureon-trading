"""
Aureon Operator — the switchboard that runs many AIs through the Aureon repo.

See ``docs/architecture/AUREON_OPERATOR_SWITCHBOARD.md`` for the full picture.

    from aureon.operator import AureonOperator, run_operator
    print(run_operator("How does Aureon integrate data across systems?").text)
"""

from aureon.operator.aureon_operator import AureonOperator, run_operator
from aureon.operator.schemas import (
    ConsensusReading,
    GroundingContext,
    OperatorResponse,
    ProviderAnswer,
)

__all__ = [
    "AureonOperator",
    "run_operator",
    "OperatorResponse",
    "ProviderAnswer",
    "GroundingContext",
    "ConsensusReading",
]
