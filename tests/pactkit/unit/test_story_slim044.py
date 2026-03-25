"""Tests for STORY-slim-044: MQ Topic Dependency."""
import textwrap


# ── MQ config detection tests (R1, R3) ───────────────────────────────

class TestParseMqConfig:
    """Test MQ topic detection from docker-compose environment vars."""

    def test_detects_kafka_topic_from_env(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              order-service:
                image: order
                environment:
                  - KAFKA_TOPIC=order-events
              notification-service:
                image: notif
                environment:
                  - KAFKA_TOPIC=order-events
                  - KAFKA_CONSUMER_GROUP=notif-group
        """), encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        topic_nodes = [n for n in g.nodes.values() if n.kind == 'topic']
        assert any('order-events' in n.label for n in topic_nodes)

    def test_detects_queue_url_from_env(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              worker:
                image: worker
                environment:
                  ORDER_QUEUE_URL: "sqs://order-queue"
        """), encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        topic_nodes = [n for n in g.nodes.values() if n.kind == 'topic']
        assert len(topic_nodes) >= 1

    def test_detects_topic_arn_from_env(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              publisher:
                image: pub
                environment:
                  EVENTS_TOPIC_ARN: "arn:aws:sns:us-east-1:123:events"
        """), encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        topic_nodes = [n for n in g.nodes.values() if n.kind == 'topic']
        assert len(topic_nodes) >= 1


# ── Publish/subscribe edge tests (R2) ────────────────────────────────

class TestPublishSubscribeEdges:
    """Test publishes and subscribes edge relations."""

    def test_publishes_and_subscribes_edges(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              order-service:
                image: order
                environment:
                  KAFKA_TOPIC: order-events
              notification-service:
                image: notif
                environment:
                  KAFKA_TOPIC: order-events
                  KAFKA_CONSUMER_GROUP: notif-group
        """), encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        pub_edges = [e for e in g.edges if e.relation == 'publishes']
        sub_edges = [e for e in g.edges if e.relation == 'subscribes']
        # order-service publishes to order-events (no consumer group)
        # notification-service subscribes to order-events (has consumer group)
        assert len(pub_edges) >= 1
        assert len(sub_edges) >= 1


# ── Source code pattern scanning tests (R4) ───────────────────────────

class TestScanMqSourcePatterns:
    """Test MQ pattern scanning in source code."""

    def test_detects_python_producer(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              order-service:
                image: order
                build: ./services/order
        """), encoding='utf-8')
        src_dir = tmp_path / 'services' / 'order'
        src_dir.mkdir(parents=True)
        (src_dir / 'publisher.py').write_text(
            'producer.send("order-events", data)\n', encoding='utf-8'
        )
        g = ServiceParser().parse(tmp_path)
        topic_nodes = [n for n in g.nodes.values() if n.kind == 'topic']
        assert any('order-events' in n.label for n in topic_nodes)

    def test_detects_java_kafka_listener(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              consumer-svc:
                image: consumer
                build: ./services/consumer
        """), encoding='utf-8')
        src_dir = tmp_path / 'services' / 'consumer'
        src_dir.mkdir(parents=True)
        (src_dir / 'Listener.java').write_text(
            '@KafkaListener(topics = "payment-events")\n', encoding='utf-8'
        )
        g = ServiceParser().parse(tmp_path)
        topic_nodes = [n for n in g.nodes.values() if n.kind == 'topic']
        assert any('payment-events' in n.label for n in topic_nodes)


# ── Impact traversal through topics (R5) ─────────────────────────────

class TestImpactThroughTopics:
    """Test reverse_reach traverses through topic nodes."""

    def test_reverse_reach_through_topic(self):
        from pactkit.skills.visualize import WorkflowNode, WorkflowEdge, WorkflowGraph
        g = WorkflowGraph()
        g.add_node(WorkflowNode(id='order-service', kind='service', label='order-service'))
        g.add_node(WorkflowNode(id='order-events', kind='topic', label='order-events'))
        g.add_node(WorkflowNode(id='notification-service', kind='service', label='notification-service'))
        g.add_edge(WorkflowEdge(source='order-service', target='order-events', relation='publishes'))
        g.add_edge(WorkflowEdge(source='order-events', target='notification-service', relation='subscribes'))
        reached = g.reverse_reach('order-service')
        # order-events points TO notification-service, so reverse from order-service
        # should find order-events (as publisher edge goes order-service -> order-events)
        # reverse_reach goes backward: who points to order-service? nobody directly
        assert 'order-service' in reached
        # Forward traversal: order-service → order-events → notification-service
        # reverse_reach from notification-service should find order-events and order-service
        reached2 = g.reverse_reach('notification-service')
        assert 'order-events' in reached2
        assert 'order-service' in reached2
