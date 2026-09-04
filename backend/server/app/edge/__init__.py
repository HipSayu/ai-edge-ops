"""Edge plane — the server side of the server<->edge protocol.

- ``gateway``  FleetGateway: binds a ``dqh.svc_core`` MessageBus to the fleet /
  observability services (heartbeat, violation, state report) + presence.
- ``runtime``  EdgePlane: picks the transport (memory | mqtt) for the app lifespan.

The wire contract itself lives in the shared ``edge_protocol`` package
(``backend/libs/edge_protocol``) — imported by both this server and the edge agent.
"""
