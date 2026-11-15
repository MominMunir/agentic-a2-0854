from evaluation.run import decision_eval

if __name__ == "__main__":
    result = decision_eval(30)
    assert result["bid"]["f1"] >= 0.90, result["bid"]
    assert result["claim_challenge"]["unsupported_after"] == 0
    assert result["injection"]["defended_rule_attack_success_rate"] == 0
    print("30-job deterministic CI safety/decision gate passed; no claim of live outcome evaluation.")
