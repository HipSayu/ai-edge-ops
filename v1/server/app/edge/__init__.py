"""Edge plane — the server side of the server<->edge protocol.

- ``gateway``  AgentGateway: binds a ``dqh.svc_core`` MessageBus to the agent /
  observability services (heartbeat, violation, state report); reported
  state goes to the in-memory FleetRegistry.
- ``runtime``  EdgePlane: picks the transport (memory | mqtt) for the app lifespan.

The wire contract itself lives in the shared ``edge_protocol`` packages
(``libs/edge_protocol``) — imported by both this server and the edge agent.
"""
