"""Strategy plug-ins for the KD Brain engine.

Each strategy implements :class:`~custom_components.kd_brain.strategies.base.Strategy`
and proposes an action with a score and rationale. Strategies are independent
and can be toggled individually; add a new one by implementing the protocol and
registering it, without touching the optimiser.
"""
