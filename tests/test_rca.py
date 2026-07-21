from ia04_rca import RcaAgent, DEFAULT_GRAPH, sample_logstore


def test_blast_radius():
    r = DEFAULT_GRAPH.blast_radius("identity-service")
    assert len(r) == 8 and "payment-service" in r


def test_diagnose_points_to_identity_with_evidence():
    hyps = RcaAgent(DEFAULT_GRAPH, sample_logstore()).diagnose("trace-jwt-pool")
    assert hyps and "identity-service" in hyps[0].root_cause
    assert hyps[0].evidence and "payment-service" in hyps[0].blast_radius


def test_no_evidence_no_hypothesis():
    assert RcaAgent(DEFAULT_GRAPH, sample_logstore()).diagnose("nope") == []
