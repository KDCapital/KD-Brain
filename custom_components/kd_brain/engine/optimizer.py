"""The KD Brain optimiser.

Collects proposals from every enabled strategy, enforces battery feasibility,
then selects the highest-scoring feasible proposal. The result is a fully
explainable :class:`Decision`: it records the considered proposals with their
scores and the reason every alternative was rejected.

This is a scoring/priority engine, not a chain of if-statements: strategies bake
their priority into the score and the optimiser simply ranks them, which keeps
new strategies pluggable.
"""

from __future__ import annotations

from ..const import SYSTEM_MODE_OBSERVE
from ..data.models import SystemState
from ..strategies.registry import enabled_strategies
from .config import OptimizerConfig
from .decision import Action, BatteryAction, Decision, Proposal


def optimize(state: SystemState, config: OptimizerConfig) -> Decision:
    """Run one optimisation round and return an explainable decision."""
    soc = state.telemetry.battery_soc_average()
    considered: list[Proposal] = []
    rejected: list[tuple[str, str]] = []

    for strategy in enabled_strategies(config):
        proposal = strategy.propose(state, config)
        if proposal is None:
            rejected.append(
                (
                    strategy.name,
                    "geen voorstel (onvoldoende data of niet van toepassing)",
                )
            )
            continue

        action = proposal.action.action
        if action is BatteryAction.CHARGE and not config.can_charge(soc):
            rejected.append(
                (strategy.name, f"batterij vol (SOC ≥ {config.battery_max_soc:.0f}%)")
            )
            continue
        if action is BatteryAction.DISCHARGE and not config.can_discharge(soc):
            rejected.append(
                (strategy.name, f"batterij leeg (SOC ≤ {config.battery_min_soc:.0f}%)")
            )
            continue

        considered.append(proposal)

    if not considered:
        return Decision(
            created=state.ts,
            mode=SYSTEM_MODE_OBSERVE,
            chosen=Action(
                device="battery",
                action=BatteryAction.IDLE,
                power_w=0,
                reason="Geen toepasbare strategie",
            ),
            strategy="none",
            why="Geen enkele ingeschakelde strategie kon een actie voorstellen",
            considered=(),
            rejected=tuple(rejected),
        )

    winner = max(considered, key=lambda p: p.score)
    for proposal in considered:
        if proposal is not winner:
            rejected.append(
                (
                    proposal.strategy,
                    f"lagere score ({proposal.score:.0f} < {winner.score:.0f})",
                )
            )

    why = (
        f"{winner.strategy} koos '{winner.action.action.value}' "
        f"(score {winner.score:.0f}): {winner.rationale}"
    )
    return Decision(
        created=state.ts,
        mode=SYSTEM_MODE_OBSERVE,
        chosen=winner.action,
        strategy=winner.strategy,
        why=why,
        considered=tuple(considered),
        rejected=tuple(rejected),
    )
