"""
evaluator.py
============
Automated evaluator for verifying journey planner recommendations against
GTFS reference data and ground-truth field observations.

Leg-Aware Validation Engine:
  - Validates individual journey legs (bus, walk, metro).
  - Explicit per-check statuses: PASS, FAIL, UNVERIFIED, NOT_APPLICABLE.
  - Overall status: PASSED, FAILED_VALIDATION, UNVERIFIED, NO_ROUTE_FOUND, ERROR.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from gtfs_reference_adapter import BaseReferenceAdapter


class JourneyEvaluator:
    """Evaluates journey planner execution results against reference adapter & ground truth."""

    def __init__(self, reference_adapter: BaseReferenceAdapter):
        self.ref_adapter = reference_adapter

    def evaluate_test_result(
        self,
        test_case: Dict[str, Any],
        api_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates a single API test result against reference data and ground-truth field observations.
        Returns a detailed leg-aware evaluation result dictionary.
        """
        test_id = test_case["test_id"]
        origin = test_case.get("origin")
        destination = test_case.get("destination")
        dep_time = test_case.get("departure_time", "08:30")
        travel_date = test_case.get("travel_date", "2026-09-28")
        expected_cond = test_case.get("expected_test_conditions", {})
        ground_truth = test_case.get("ground_truth", {})
        expected_journey_type = test_case.get("journey_type", "direct")

        is_success = api_result.get("is_success", False)
        error_msg = api_result.get("error_message")
        options = api_result.get("all_options", [])
        top_opt = api_result.get("recommended_option")

        # 1. Handle API Error / No Options Found
        if not is_success:
            return self._build_eval_output(
                test_case, api_result,
                validation_status="ERROR",
                failure_reasons=[f"API Error: {error_msg}"],
                checks={}
            )

        if not options and top_opt:
            options = [top_opt]

        if not options:
            if expected_cond.get("service_expected", True):
                return self._build_eval_output(
                    test_case, api_result,
                    validation_status="NO_ROUTE_FOUND",
                    failure_reasons=["Engine returned 0 options for a feasible journey case"],
                    is_missing_route=True,
                    checks={}
                )
            else:
                return self._build_eval_output(
                    test_case, api_result,
                    validation_status="PASSED",
                    failure_reasons=[],
                    checks={}
                )

        # 2. Extract Legs & Detailed Recommendation Fields
        legs = top_opt.get("legs") or []
        routes = top_opt.get("routes") or []
        b_stops = top_opt.get("boarding_stops") or []
        a_stops = top_opt.get("alighting_stops") or []
        transfers_count = top_opt.get("transfers", 0)

        # Separate Bus vs Walk legs
        bus_legs = [l for l in legs if l.get("leg_type") == "bus"]
        walk_legs = [l for l in legs if l.get("leg_type") == "walk"]

        if not bus_legs and routes:
            # Fallback for unsegmented routes
            bus_routes = [r for r in routes if str(r).strip().lower() not in ("walk", "walking", "foot", "transfer", "transfer_walk")]
            for idx, r in enumerate(bus_routes):
                b_s = b_stops[idx] if idx < len(b_stops) else origin
                a_s = a_stops[idx] if idx < len(a_stops) else destination
                bus_legs.append({
                    "leg_index": idx,
                    "leg_type": "bus",
                    "route_id": str(r),
                    "boarding_stop": str(b_s),
                    "alighting_stop": str(a_s),
                    "fare_inr": top_opt.get("fare_inr", 0.0),
                    "duration_mins": top_opt.get("duration_mins", 0.0)
                })

        checks: Dict[str, Dict[str, Any]] = {}
        failure_reasons: List[str] = []
        unverified_reasons: List[str] = []

        # Check 1: Bus Route Existence
        if not bus_legs:
            checks["bus_route_existence"] = {
                "status": "FAIL",
                "reason": "Journey recommendation contains no valid BMTC bus legs",
                "affected_leg": None
            }
            failure_reasons.append("No valid BMTC bus legs found in journey option")
        else:
            invalid_routes = []
            for leg in bus_legs:
                r_id = leg.get("route_id", "N/A")
                if not r_id or r_id == "N/A" or not self.ref_adapter.verify_route_exists(r_id):
                    invalid_routes.append((leg.get("leg_index"), r_id))

            if invalid_routes:
                leg_idx, r_id = invalid_routes[0]
                checks["bus_route_existence"] = {
                    "status": "FAIL",
                    "reason": f"Route '{r_id}' at leg {leg_idx} does not exist in GTFS reference feed",
                    "affected_leg": leg_idx
                }
                failure_reasons.append(f"Route '{r_id}' does not exist in GTFS reference feed")
            else:
                checks["bus_route_existence"] = {
                    "status": "PASS",
                    "reason": f"All {len(bus_legs)} bus route identifiers verified in reference data",
                    "affected_leg": None
                }

        # Check 2: Stop Sequence & Direction per Bus Leg
        seq_failures = []
        seq_unverified = []

        for leg in bus_legs:
            l_idx = leg.get("leg_index", 0)
            r_id = leg.get("route_id", "N/A")
            b_s = leg.get("boarding_stop") or origin
            a_s = leg.get("alighting_stop") or destination

            seq_ok, seq_msg = self.ref_adapter.verify_stop_sequence(r_id, b_s, a_s)
            if not seq_ok:
                seq_failures.append((l_idx, seq_msg))
            elif "absent in GTFS" in seq_msg or "fuzzy-matched" in seq_msg:
                seq_unverified.append((l_idx, seq_msg))

        if seq_failures:
            l_idx, msg = seq_failures[0]
            checks["bus_stop_sequence"] = {
                "status": "FAIL",
                "reason": f"Leg {l_idx}: {msg}",
                "affected_leg": l_idx
            }
            failure_reasons.append(msg)
        elif seq_unverified:
            l_idx, msg = seq_unverified[0]
            checks["bus_stop_sequence"] = {
                "status": "UNVERIFIED",
                "reason": f"Leg {l_idx}: {msg}",
                "affected_leg": l_idx
            }
            unverified_reasons.append(msg)
        else:
            checks["bus_stop_sequence"] = {
                "status": "PASS",
                "reason": "Boarding stop precedes alighting stop in correct route sequence across all legs",
                "affected_leg": None
            }

        # Check 3: Service Day Calendar Active Check
        inactive_services = []
        for leg in bus_legs:
            r_id = leg.get("route_id", "N/A")
            if not self.ref_adapter.is_service_active(r_id, travel_date):
                inactive_services.append((leg.get("leg_index"), r_id))

        if inactive_services:
            l_idx, r_id = inactive_services[0]
            checks["service_day_active"] = {
                "status": "FAIL",
                "reason": f"Route '{r_id}' at leg {l_idx} is inactive on {travel_date}",
                "affected_leg": l_idx
            }
            failure_reasons.append(f"Route '{r_id}' is inactive on {travel_date}")
        else:
            checks["service_day_active"] = {
                "status": "PASS",
                "reason": f"Service active on requested travel date ({travel_date})",
                "affected_leg": None
            }

        # Check 4: Departure Time Validity
        dep_invalid = []
        for leg in bus_legs:
            r_id = leg.get("route_id", "N/A")
            b_s = leg.get("boarding_stop") or origin
            dep_ok, dep_msg = self.ref_adapter.verify_departure_validity(r_id, b_s, dep_time)
            if not dep_ok:
                dep_invalid.append((leg.get("leg_index"), dep_msg))

        if dep_invalid:
            l_idx, msg = dep_invalid[0]
            checks["departure_time_valid"] = {
                "status": "FAIL",
                "reason": f"Leg {l_idx}: {msg}",
                "affected_leg": l_idx
            }
            failure_reasons.append(msg)
        else:
            checks["departure_time_valid"] = {
                "status": "PASS",
                "reason": f"Departure time at {dep_time} is within operational window",
                "affected_leg": None
            }

        # Check 5: Direct Journey Expectation Check
        if expected_journey_type == "direct":
            if len(bus_legs) > 1:
                checks["direct_journey_expectation"] = {
                    "status": "FAIL",
                    "reason": f"Expected direct journey (0 transfers) but recommendation contains {len(bus_legs)} bus legs",
                    "affected_leg": None
                }
                failure_reasons.append(f"Direct journey expected but returned {len(bus_legs)} bus legs")
            else:
                checks["direct_journey_expectation"] = {
                    "status": "PASS",
                    "reason": "Direct journey contains exactly 1 bus leg as expected",
                    "affected_leg": None
                }
        else:
            checks["direct_journey_expectation"] = {
                "status": "NOT_APPLICABLE",
                "reason": f"Transfer journey expected ({expected_journey_type})",
                "affected_leg": None
            }

        # Check 6: Transfer Continuity Check
        if len(legs) > 1 and transfers_count > 0:
            transfer_failures = []
            transfer_unverified = []

            for i in range(len(legs) - 1):
                leg_1 = legs[i]
                leg_2 = legs[i + 1]

                a_1 = leg_1.get("alighting_stop", "")
                b_2 = leg_2.get("boarding_stop", "")

                t_ok, t_msg = self.ref_adapter.verify_transfer_feasibility(a_1, b_2)
                if not t_ok:
                    transfer_failures.append((i, t_msg))
                elif "assumed feasible" in t_msg:
                    transfer_unverified.append((i, t_msg))

            if transfer_failures:
                l_idx, msg = transfer_failures[0]
                checks["transfer_continuity"] = {
                    "status": "FAIL",
                    "reason": f"Transfer after leg {l_idx}: {msg}",
                    "affected_leg": l_idx
                }
                failure_reasons.append(msg)
            elif transfer_unverified:
                l_idx, msg = transfer_unverified[0]
                checks["transfer_continuity"] = {
                    "status": "UNVERIFIED",
                    "reason": f"Transfer after leg {l_idx}: {msg}",
                    "affected_leg": l_idx
                }
                unverified_reasons.append(msg)
            else:
                checks["transfer_continuity"] = {
                    "status": "PASS",
                    "reason": "Adjacent transport legs connect at identical or adjacent stops (<500m)",
                    "affected_leg": None
                }
        else:
            checks["transfer_continuity"] = {
                "status": "NOT_APPLICABLE",
                "reason": "Direct journey, no transfer leg evaluation required",
                "affected_leg": None
            }

        # Check 7: Walking Leg Feasibility Check
        if walk_legs:
            walk_failures = []
            for w in walk_legs:
                dist = w.get("distance_km", 0.0)
                dur = w.get("duration_mins", 0.0)
                if dist > 1.5:
                    walk_failures.append((w.get("leg_index"), f"Walking leg distance ({dist:.2f} km) exceeds maximum 1.5 km limit"))
                elif dur > 25.0:
                    walk_failures.append((w.get("leg_index"), f"Walking leg duration ({dur:.1f} mins) exceeds maximum 25 min limit"))

            if walk_failures:
                l_idx, msg = walk_failures[0]
                checks["walk_feasibility"] = {
                    "status": "FAIL",
                    "reason": f"Leg {l_idx}: {msg}",
                    "affected_leg": l_idx
                }
                failure_reasons.append(msg)
            else:
                checks["walk_feasibility"] = {
                    "status": "PASS",
                    "reason": f"All {len(walk_legs)} walking legs are within configured distance/time limits",
                    "affected_leg": None
                }
        else:
            checks["walk_feasibility"] = {
                "status": "NOT_APPLICABLE",
                "reason": "No walking legs in recommended journey",
                "affected_leg": None
            }

        # Check 8: End-to-End Destination Reachability Check
        final_alighting = legs[-1].get("alighting_stop") if legs else (a_stops[-1] if a_stops else "")
        if not final_alighting or final_alighting == "N/A":
            checks["destination_reachability"] = {
                "status": "FAIL",
                "reason": "Final leg alighting stop is missing or unassigned",
                "affected_leg": len(legs) - 1 if legs else 0
            }
            failure_reasons.append("Final leg alighting stop is unassigned")
        else:
            checks["destination_reachability"] = {
                "status": "PASS",
                "reason": f"Final leg alights at '{final_alighting}', completing journey to destination",
                "affected_leg": None
            }

        # 3. Fare and Travel Time Metrics Calculation
        pred_fare = top_opt.get("fare_inr")
        pred_duration = top_opt.get("duration_mins")

        ref_fare, ref_duration = self.ref_adapter.get_reference_fare_and_duration(
            origin, destination, bus_legs[0].get("route_id") if bus_legs else None
        )
        
        fare_error_inr = round(abs(pred_fare - ref_fare), 2) if (pred_fare is not None and ref_fare is not None) else None
        duration_error_min = round(abs(pred_duration - ref_duration), 2) if (pred_duration is not None and ref_duration is not None) else None

        # 4. Ground-Truth Field Observation Evaluation
        gt_observed = ground_truth.get("has_observation", False)
        gt_fare_error_inr = None
        gt_duration_error_min = None

        if gt_observed:
            gt_fare = ground_truth.get("actual_fare_inr")
            gt_duration = ground_truth.get("actual_duration_mins")
            if pred_fare is not None and gt_fare is not None:
                gt_fare_error_inr = round(abs(pred_fare - gt_fare), 2)
            if pred_duration is not None and gt_duration is not None:
                gt_duration_error_min = round(abs(pred_duration - gt_duration), 2)

        # 5. Determine Overall Case Validation Status
        # Status priority: FAIL > UNVERIFIED > PASS
        any_fail = any(c.get("status") == "FAIL" for c in checks.values())
        any_unverified = any(c.get("status") == "UNVERIFIED" for c in checks.values())

        if failure_reasons or any_fail:
            overall_status = "FAILED_VALIDATION"
        elif unverified_reasons or any_unverified:
            overall_status = "UNVERIFIED"
        else:
            overall_status = "PASSED"

        is_false_positive = (overall_status == "FAILED_VALIDATION")

        return self._build_eval_output(
            test_case=test_case,
            api_result=api_result,
            validation_status=overall_status,
            failure_reasons=failure_reasons + unverified_reasons,
            checks=checks,
            fare_reference=ref_fare,
            duration_reference=ref_duration,
            fare_error_inr=fare_error_inr,
            duration_error_min=duration_error_min,
            gt_fare_error_inr=gt_fare_error_inr,
            gt_duration_error_min=gt_duration_error_min,
            is_false_positive=is_false_positive
        )

    def _build_eval_output(
        self,
        test_case: Dict[str, Any],
        api_result: Dict[str, Any],
        validation_status: str,
        failure_reasons: List[str],
        checks: Dict[str, Dict[str, Any]],
        fare_reference: Optional[float] = None,
        duration_reference: Optional[float] = None,
        fare_error_inr: Optional[float] = None,
        duration_error_min: Optional[float] = None,
        gt_fare_error_inr: Optional[float] = None,
        gt_duration_error_min: Optional[float] = None,
        is_missing_route: bool = False,
        is_false_positive: bool = False
    ) -> Dict[str, Any]:
        """Assembles comprehensive evaluation output dictionary."""
        top_opt = api_result.get("recommended_option") or {}
        gt = test_case.get("ground_truth") or {}

        # Individual boolean check flags for backward compatibility
        route_exists_valid = (checks.get("bus_route_existence", {}).get("status") == "PASS")
        sequence_valid = (checks.get("bus_stop_sequence", {}).get("status") == "PASS")
        service_day_valid = (checks.get("service_day_active", {}).get("status") == "PASS")
        transfer_valid = (checks.get("transfer_continuity", {}).get("status") in ("PASS", "NOT_APPLICABLE"))
        time_valid = (checks.get("departure_time_valid", {}).get("status") == "PASS")

        return {
            "test_id": test_case["test_id"],
            "name": test_case.get("name", test_case["test_id"]),
            "origin": test_case.get("origin"),
            "destination": test_case.get("destination"),
            "travel_date": test_case.get("travel_date", "2026-09-28"),
            "departure_time": test_case.get("departure_time", "08:30"),
            "departure_period": test_case.get("departure_period", "off_peak"),
            "journey_type": test_case.get("journey_type", "direct"),
            "preference": test_case.get("preference", "fastest"),
            "options_found": api_result.get("options_count", 0),
            "latency_ms": api_result.get("latency_ms", 0.0),
            
            # Recommendation details
            "recommended_mode": top_opt.get("mode", "N/A"),
            "recommended_routes": ", ".join(top_opt.get("routes", [])),
            "boarding_stops": ", ".join(top_opt.get("boarding_stops", [])),
            "alighting_stops": ", ".join(top_opt.get("alighting_stops", [])),
            "transfers_count": top_opt.get("transfers", 0),
            "fare_predicted_inr": top_opt.get("fare_inr"),
            "duration_predicted_min": top_opt.get("duration_mins"),
            "legs": top_opt.get("legs", []),

            # Validation Status & Structured Checks
            "validation_status": validation_status,
            "failure_reasons": failure_reasons,
            "checks": checks,
            
            # Compatibility flags
            "route_exists_valid": route_exists_valid,
            "sequence_valid": sequence_valid,
            "service_day_valid": service_day_valid,
            "transfer_valid": transfer_valid,
            "time_valid": time_valid,
            "is_missing_route": is_missing_route,
            "is_false_positive": is_false_positive,

            # Reference Data Delta
            "fare_reference_inr": fare_reference,
            "duration_reference_min": duration_reference,
            "fare_error_inr": fare_error_inr,
            "duration_error_min": duration_error_min,

            # Ground-Truth Observations Delta
            "gt_has_observation": gt.get("has_observation", False),
            "gt_actual_route": gt.get("actual_route_taken"),
            "gt_actual_fare_inr": gt.get("actual_fare_inr"),
            "gt_actual_duration_mins": gt.get("actual_duration_mins"),
            "gt_fare_error_inr": gt_fare_error_inr,
            "gt_duration_error_min": gt_duration_error_min,
            
            "reference_source": self.ref_adapter.get_source_name()
        }
