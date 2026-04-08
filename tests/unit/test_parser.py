"""Unit tests for the robust parser contract."""

import pytest
from utils.parser import parse_llm_action
from utils.schemas import ParsedAction
from utils.constants import PARSER_DEFAULT_U, PARSER_DEFAULT_F, INVALID_ACTION_PENALTY


def test_valid_json():
    text = '{"U_target": 0.3, "F_target": 0.7}'
    result = parse_llm_action(text)
    assert result.u_target == 0.3
    assert result.f_target == 0.7
    assert result.source == "json"
    assert result.invalid_output is False
    assert result.penalty_applied == 0.0
    assert result.parse_error is None

def test_json_missing_keys():
    text = '{"U_target": 0.3}'
    result = parse_llm_action(text)
    assert result.source == "default"
    assert result.invalid_output is True
    assert result.penalty_applied == -INVALID_ACTION_PENALTY
    assert result.parse_error is not None and "missing required keys" in result.parse_error
    assert result.u_target == PARSER_DEFAULT_U
    assert result.f_target == PARSER_DEFAULT_F

def test_anchored_extraction():
    # Quoted
    text1 = 'Here is the action: "U_target":0.3 and later "F_target":0.7.'
    result1 = parse_llm_action(text1)
    assert result1.source == "fallback"
    assert result1.invalid_output is True
    assert result1.u_target == 0.3
    assert result1.f_target == 0.7

    # Unquoted with equals
    text2 = 'U_target = 0.2, F_target = 0.8'
    result2 = parse_llm_action(text2)
    assert result2.source == "fallback"
    assert result2.invalid_output is True
    assert result2.u_target == 0.2
    assert result2.f_target == 0.8

    # Unquoted with space and case insensitivity
    text3 = 'u_target 0.1 f_target 0.9'
    result3 = parse_llm_action(text3)
    assert result3.source == "fallback"
    assert result3.invalid_output is True
    assert result3.u_target == 0.1
    assert result3.f_target == 0.9

def test_pair_format():
    # Whitespace
    text1 = ' 0.3 0.7 '
    result1 = parse_llm_action(text1)
    assert result1.source == "fallback"
    assert result1.invalid_output is False
    assert result1.penalty_applied == 0.0
    assert result1.u_target == 0.3
    assert result1.f_target == 0.7

    # Comma separation
    text2 = '0.3,0.7'
    result2 = parse_llm_action(text2)
    assert result2.source == "fallback"
    assert result2.invalid_output is False
    assert result2.u_target == 0.3
    assert result2.f_target == 0.7

    # Semicolon
    text3 = '0.3; 0.7'
    result3 = parse_llm_action(text3)
    assert result3.source == "fallback"
    assert result3.invalid_output is False
    assert result3.u_target == 0.3
    assert result3.f_target == 0.7

def test_out_of_range_clamping():
    text = '{"U_target": -1.0, "F_target": 2.0}'
    result = parse_llm_action(text)
    assert result.source == "json"
    assert result.u_target == 0.0
    assert result.f_target == 1.0

def test_empty_string_fallback():
    text = ''
    result = parse_llm_action(text, previous_valid_action=None)
    assert result.source == "default"
    assert result.invalid_output is True
    assert result.penalty_applied == -INVALID_ACTION_PENALTY
    assert result.u_target == PARSER_DEFAULT_U
    assert result.f_target == PARSER_DEFAULT_F

def test_previous_valid_action():
    text = 'invalid nonsens'
    prev_action = {"U_target": 0.45, "F_target": 0.55}
    result = parse_llm_action(text, previous_valid_action=prev_action)
    assert result.source == "previous_valid"
    assert result.invalid_output is True
    assert result.penalty_applied == -INVALID_ACTION_PENALTY
    assert result.u_target == 0.45
    assert result.f_target == 0.55
