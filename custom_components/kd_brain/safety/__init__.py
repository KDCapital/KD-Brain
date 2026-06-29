"""Safety layer: the mandatory gate every actuation must pass.

The safety layer is independent of the strategies and the optimiser. It clamps
and, when necessary, blocks actions to protect the battery and hardware (SOC
limits, power limits, anti-oscillation, write-throttling, hysteresis). It can
never be overridden by a strategy.
"""
