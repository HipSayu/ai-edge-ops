from hopquangdo.messaging import TopicMatcher

from src.shared.contracts import CommandType, EdgeTopics


def test_topic_matcher():
    assert TopicMatcher.matches("edge/+/+/telemetry/+", "edge/c/n/telemetry/system")
    assert TopicMatcher.matches("edge/+/+/state/#", "edge/c/n/state")
    assert TopicMatcher.matches("edge/+/+/state/#", "edge/c/n/state/runtime")
    assert not TopicMatcher.matches("edge/+/+/event/+", "edge/c/n/telemetry/gpu")


def test_edge_topics_roundtrip():
    t = EdgeTopics("c1", "n1")
    assert t.command(CommandType.DEPLOY) == "edge/c1/n1/command/deploy"
    addr = EdgeTopics.parse(t.telemetry("gpu"))
    assert (addr.cluster_id, addr.node_id, addr.channel, addr.kind) == ("c1", "n1", "telemetry", "gpu")
    assert EdgeTopics.parse(t.state()).kind is None

