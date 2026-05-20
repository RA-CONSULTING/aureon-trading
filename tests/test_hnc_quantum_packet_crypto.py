import json

import pytest

from aureon.harmonic.hnc_quantum_packet_crypto import (
    ENV_PACKET_PREFIX,
    HNCPacketError,
    build_hnc_swarm_packet,
    build_hnc_quantum_packet,
    decode_env_packet,
    decode_hnc_quantum_packet,
    decode_hnc_swarm_packet,
    encode_env_packet,
    env_packet_summary,
    reassemble_hnc_probability_fragments,
    run_hnc_packet_breaker_checks,
    run_hnc_swarm_breaker_checks,
    stream_hnc_probability_fragments,
    validate_hnc_packet_contract,
)


MASTER_KEY = "test-master-key-for-hnc-packets-32-bytes"


def test_hnc_quantum_packet_round_trips_without_exposing_plaintext():
    packet = build_hnc_quantum_packet(
        "kraken-secret-value",
        MASTER_KEY,
        purpose="env:KRAKEN_API_SECRET",
        operator_aad={"env_key": "KRAKEN_API_SECRET"},
    )

    packet_text = json.dumps(packet)
    validation = validate_hnc_packet_contract(packet)
    decoded = decode_hnc_quantum_packet(
        packet,
        MASTER_KEY,
        expected_purpose="env:KRAKEN_API_SECRET",
        expected_operator_aad={"env_key": "KRAKEN_API_SECRET"},
    )

    assert validation["valid"] is True
    assert validation["auris_node_count"] == 9
    assert decoded.text() == "kraken-secret-value"
    assert "kraken-secret-value" not in packet_text
    assert decoded.decode_report["packet_contract"]["valid"] is True


def test_hnc_packet_rejects_geometry_tamper():
    packet = build_hnc_quantum_packet("secret", MASTER_KEY)
    packet["metadata"]["hnc_alignment"]["geometry"]["profit_anchor_hz"] = 189.0

    with pytest.raises(HNCPacketError):
        decode_hnc_quantum_packet(packet, MASTER_KEY)


def test_env_packet_round_trip_and_summary():
    token = encode_env_packet("binance-secret", MASTER_KEY, env_key="BINANCE_API_SECRET")
    summary = env_packet_summary(token)

    assert token.startswith(ENV_PACKET_PREFIX)
    assert summary["encoded"] is True
    assert summary["valid_contract"] is True
    assert decode_env_packet(token, MASTER_KEY, env_key="BINANCE_API_SECRET") == "binance-secret"
    assert "binance-secret" not in token


def test_breaker_checks_reject_all_tamper_attempts():
    packet = build_hnc_quantum_packet("capital-password", MASTER_KEY, purpose="env:CAPITAL_PASSWORD")
    report = run_hnc_packet_breaker_checks(packet, MASTER_KEY)

    assert report["passed"] is True
    assert {check["name"] for check in report["checks"]} == {
        "ciphertext_bit_flip",
        "geometry_frequency_tamper",
        "purpose_tamper",
        "operator_aad_tamper",
        "packet_hash_tamper",
        "temporal_fragment_missing",
        "temporal_fragment_tamper",
    }


def test_probability_fragments_reassemble_before_decode():
    packet = build_hnc_quantum_packet("superposition-secret", MASTER_KEY, purpose="hnc:test")
    fragments = stream_hnc_probability_fragments(packet, fragment_size=256)

    assert len(fragments) > 1
    assert all(fragment["stream_type"] == "hnc_temporal_probability_fragment" for fragment in fragments)
    assert "superposition-secret" not in json.dumps(fragments)
    assert round(sum(fragment["probability_weight"] for fragment in fragments), 6) == 1.0

    reassembled = reassemble_hnc_probability_fragments(list(reversed(fragments)))
    decoded = decode_hnc_quantum_packet(reassembled, MASTER_KEY, expected_purpose="hnc:test")

    assert reassembled["packet_sha256"] == packet["packet_sha256"]
    assert decoded.text() == "superposition-secret"


def test_probability_fragments_reject_missing_piece():
    packet = build_hnc_quantum_packet("cannot-collapse-yet", MASTER_KEY, purpose="hnc:test")
    fragments = stream_hnc_probability_fragments(packet, fragment_size=256)

    with pytest.raises(HNCPacketError):
        reassemble_hnc_probability_fragments(fragments[:-1])


def test_hnc_swarm_packet_requires_two_agent_locknotes():
    agents = {
        "seer": "seer-master-key-32-bytes-for-test",
        "lyra": "lyra-master-key-32-bytes-for-test",
        "king": "king-master-key-32-bytes-for-test",
    }
    packet = build_hnc_swarm_packet(
        "swarm-secret",
        agents,
        purpose="hnc:swarm",
        operator_aad={"intent": "two_way_security"},
    )

    with pytest.raises(HNCPacketError):
        decode_hnc_swarm_packet(packet, {"seer": agents["seer"]}, expected_purpose="hnc:swarm")

    decoded = decode_hnc_swarm_packet(
        packet,
        {"seer": agents["seer"], "lyra": agents["lyra"]},
        expected_purpose="hnc:swarm",
        expected_operator_aad={"intent": "two_way_security"},
    )

    assert decoded.text() == "swarm-secret"
    assert decoded.decode_report["swarm_mode"] == "hnc_swarm_two_way_locknotes_v1"
    assert decoded.decode_report["single_agent_can_decode"] is False
    assert len(packet["swarm_locknotes"]) == 6
    assert "swarm-secret" not in json.dumps(packet)


def test_hnc_swarm_breaker_checks_reject_breach_paths():
    agents = {
        "seer": "seer-master-key-32-bytes-for-test",
        "lyra": "lyra-master-key-32-bytes-for-test",
        "king": "king-master-key-32-bytes-for-test",
    }
    packet = build_hnc_swarm_packet("breach-test-secret", agents, purpose="hnc:swarm")
    report = run_hnc_swarm_breaker_checks(packet, agents)

    assert report["passed"] is True
    assert {check["name"] for check in report["checks"]} == {
        "valid_two_agent_pair_decode",
        "single_agent_decode_blocked",
        "wrong_agent_secret_blocked",
        "locknote_tamper_blocked",
        "missing_pair_locknote_blocked",
    }
