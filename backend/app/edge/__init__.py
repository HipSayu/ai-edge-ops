"""Edge plane: the server side of the server<->edge protocol.

- ``protocol``  — message payloads + topic scheme (domain-specific, lives here not in svc_core)
- ``gateway``   — FleetGateway: wires a svc_core MessageBus to the fleet/observability services
"""
