# SaaS Compliance Audit

**Status:** compliant · 15/15 checks passed

| Check | Result | Detail |
|-------|--------|--------|
| stamped:/api/status | ✅ | provenance=True truth_status=live |
| stamped:/api/organism | ✅ | provenance=True truth_status=live |
| stamped:/api/metacognition | ✅ | provenance=True truth_status=real_derived |
| stamped:/api/catalog | ✅ | provenance=True truth_status=real_derived |
| stamped:/api/domains | ✅ | provenance=True truth_status=real_derived |
| stamped:/api/cognition | ✅ | surfaces=['brain', 'bus', 'connectome', 'field', 'mycelium'] all_stamped=True |
| stamped:/api/cognition/field | ✅ | truth_status=cached_real |
| stamped:/api/cognition/bus | ✅ | truth_status=live |
| stamped:/api/cognition/mycelium | ✅ | truth_status=live |
| stamped:/api/cognition/connectome | ✅ | truth_status=live |
| stamped:/api/cognition/brain | ✅ | truth_status=real_derived |
| catalog_honest | ✅ | category_count=12 unique_total=1315 Σcategories=3639 |
| charge_fee_disabled | ✅ | status=403 (expected 403 when AUREON_BILLING_CHARGE_ENABLED unset) |
| provenance_reflects_policy | ✅ | sim_fallback=False |
| saas_no_fabrication | ✅ | clean |
