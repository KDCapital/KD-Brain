"""Optional exact battery-arbitrage optimiser using HiGHS (highspy).

This solves a linear program over the whole remaining price horizon to find the
cost-optimal charge/discharge schedule, accounting for round-trip losses,
battery degradation and the SOC trajectory, then takes the action for *now*.

``highspy`` is an optional dependency: it is imported lazily and only used when
the user selects the MILP optimiser mode. If it is not installed,
:class:`MilpUnavailableError` is raised so the caller can fall back to the heuristic
optimiser and surface a repair.
"""

from __future__ import annotations

from ..const import SYSTEM_MODE_OBSERVE
from ..data.models import SystemState
from .config import OptimizerConfig
from .decision import Action, BatteryAction, Decision

# Treat sub-50 W net power as idle.
_IDLE_W = 50


class MilpUnavailableError(RuntimeError):
    """Raised when the optional highspy solver is not installed."""


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def milp_optimize(state: SystemState, config: OptimizerConfig) -> Decision | None:
    """Return an exact LP-optimised decision, or None if inputs are insufficient.

    Raises :class:`MilpUnavailableError` when highspy is not installed.
    """
    try:
        import highspy  # noqa: PLC0415  (lazy, optional dependency)
    except ImportError as err:
        raise MilpUnavailableError("highspy is not installed") from err

    points = state.prices.points
    capacity_wh = state.telemetry.battery_capacity_total()
    if not points or not capacity_wh:
        return None

    cap = capacity_wh / 1000.0  # kWh
    soc_min = config.battery_min_soc / 100.0 * cap
    soc_max = config.battery_max_soc / 100.0 * cap
    if soc_min >= soc_max:
        return None

    soc_pct = state.telemetry.battery_soc_average()
    soc0 = _clamp(
        (soc_pct / 100.0 if soc_pct is not None else 0.5) * cap, soc_min, soc_max
    )

    eff = _clamp(float(config.roundtrip_efficiency), 0.1, 1.0)
    leg = eff**0.5  # split round-trip efficiency over charge and discharge
    deg = float(config.degradation_cost)  # €/kWh throughput
    p_charge = config.max_charge_w / 1000.0  # kW
    p_discharge = config.max_discharge_w / 1000.0

    n = len(points)
    solver = highspy.Highs()
    solver.setOptionValue("output_flag", False)

    charge = [solver.addVariable(lb=0, ub=p_charge) for _ in range(n)]
    discharge = [solver.addVariable(lb=0, ub=p_discharge) for _ in range(n)]
    soc = [solver.addVariable(lb=soc_min, ub=soc_max) for _ in range(n + 1)]

    solver.addConstr(soc[0] == soc0)
    objective = []
    for t, point in enumerate(points):
        hours = (point.end - point.start).total_seconds() / 3600.0
        solver.addConstr(
            soc[t + 1]
            == soc[t] + charge[t] * leg * hours - discharge[t] * (1.0 / leg) * hours
        )
        buy = float(point.all_in)
        sell = float(point.all_in)  # discharging avoids importing at all-in
        objective.append(charge[t] * (hours * (buy + deg)))
        objective.append(discharge[t] * (hours * (deg - sell)))

    solver.minimize(sum(objective))
    if str(solver.getModelStatus()) != "HighsModelStatus.kOptimal":
        return None

    net_kw = solver.variableValue(charge[0]) - solver.variableValue(discharge[0])
    net_w = round(net_kw * 1000)

    if net_w > _IDLE_W:
        action = Action("battery", BatteryAction.CHARGE, net_w, "MILP-schema: laden")
    elif net_w < -_IDLE_W:
        action = Action(
            "battery", BatteryAction.DISCHARGE, -net_w, "MILP-schema: ontladen"
        )
    else:
        action = Action("battery", BatteryAction.IDLE, 0, "MILP-schema: wachten")

    return Decision(
        created=state.ts,
        mode=SYSTEM_MODE_OBSERVE,
        chosen=action,
        strategy="milp",
        why=(
            f"MILP-optimalisatie over {n} prijsslots: kostenoptimaal "
            f"{action.action.value} ({abs(net_w)} W)"
        ),
        considered=(),
        rejected=(),
    )
