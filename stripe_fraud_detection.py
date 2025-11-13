#!/bin/python3

#
# Complete the 'find_fraudulent_merchants' function below.
#
# The function is expected to return a STRING.
# The function accepts following parameters:
#  1. STRING non_fraud_codes
#  2. STRING fraud_codes
#  3. STRING ARRAY mcc_thresholds
#  4. STRING ARRAY merchant_mcc_map
#  5. STRING min_charges
#  6. STRING ARRAY charges
#

def find_fraudulent_merchants(non_fraud_codes, fraud_codes, mcc_thresholds, merchant_mcc_map, min_charges, charges):
    """
    Detect fraudulent merchants based on transaction patterns.

    Supports three modes:
    - Part 1: Count-based thresholds (integer thresholds)
    - Part 2: Percentage-based thresholds (decimal thresholds) with sticky fraudulent status
    - Part 3: Dispute handling that can restore merchant status
    """
    # Parse fraud/non-fraud code sets
    non_fraud_set = set(code.strip() for code in non_fraud_codes.split(',') if code.strip())
    fraud_set = set(code.strip() for code in fraud_codes.split(',') if code.strip())

    # Parse MCC thresholds
    mcc_threshold_map = {}
    is_percentage_mode = False

    for row in mcc_thresholds:
        if not row.strip():
            continue
        parts = row.split(',')
        mcc = parts[0].strip()
        threshold_str = parts[1].strip()

        # Determine if percentage (float) or count (int)
        if '.' in threshold_str:
            mcc_threshold_map[mcc] = float(threshold_str)
            is_percentage_mode = True
        else:
            mcc_threshold_map[mcc] = int(threshold_str)

    # Parse merchant MCC mapping
    merchant_mcc = {}
    for row in merchant_mcc_map:
        if not row.strip():
            continue
        parts = row.split(',')
        account_id = parts[0].strip()
        mcc = parts[1].strip()
        merchant_mcc[account_id] = mcc

    # Parse minimum charges
    min_charges_count = int(min_charges.strip())

    # Track merchant statistics
    merchant_stats = {}  # account_id -> {total_count, fraud_count, is_fraudulent}
    charge_registry = {}  # charge_id -> {account_id, is_fraud_original, is_fraud_current}
    fraudulent_merchants = set()

    def should_mark_fraudulent(account_id):
        """Check if merchant meets criteria to be marked fraudulent."""
        if account_id not in merchant_mcc:
            return False

        mcc = merchant_mcc[account_id]

        # Get threshold for this MCC
        if mcc in mcc_threshold_map:
            threshold = mcc_threshold_map[mcc]
        elif not is_percentage_mode:
            # Count mode: use default threshold of 1 for undefined MCCs
            threshold = 1
        else:
            # Percentage mode: skip evaluation if MCC not defined
            return False

        stats = merchant_stats[account_id]
        total = stats['total_count']
        fraud_count = stats['fraud_count']

        # Only evaluate if we've seen enough transactions
        if total < min_charges_count:
            return False

        if is_percentage_mode:
            # Percentage-based threshold
            fraud_ratio = fraud_count / total if total > 0 else 0
            return fraud_ratio >= threshold
        else:
            # Count-based threshold
            return fraud_count >= threshold

    def should_clear_fraudulent(account_id):
        """Check if merchant should have fraudulent status cleared."""
        if not merchant_stats[account_id]['is_fraudulent']:
            return False

        # Only for percentage mode with disputes
        if not is_percentage_mode:
            return False

        if account_id not in merchant_mcc:
            return False

        mcc = merchant_mcc[account_id]
        if mcc not in mcc_threshold_map:
            return False

        threshold = mcc_threshold_map[mcc]
        stats = merchant_stats[account_id]
        total = stats['total_count']
        fraud_count = stats['fraud_count']

        # Check if still meets minimum transaction count
        if total < min_charges_count:
            return False

        fraud_ratio = fraud_count / total if total > 0 else 0
        # Clear if now below threshold
        return fraud_ratio < threshold

    # Process charges and disputes in order
    for row in charges:
        if not row.strip():
            continue

        parts = row.split(',')
        operation = parts[0].strip()

        if operation == 'CHARGE':
            charge_id = parts[1].strip()
            account_id = parts[2].strip()
            amount = parts[3].strip()
            code = parts[4].strip()

            # Initialize merchant stats if first time seeing this merchant
            if account_id not in merchant_stats:
                merchant_stats[account_id] = {
                    'total_count': 0,
                    'fraud_count': 0,
                    'is_fraudulent': False
                }

            # Determine if this charge is fraudulent
            is_fraud = code in fraud_set

            # Register the charge
            charge_registry[charge_id] = {
                'account_id': account_id,
                'is_fraud_original': is_fraud,
                'is_fraud_current': is_fraud
            }

            # Update merchant statistics
            merchant_stats[account_id]['total_count'] += 1
            if is_fraud:
                merchant_stats[account_id]['fraud_count'] += 1

            # Check if merchant should be marked fraudulent
            if not merchant_stats[account_id]['is_fraudulent']:
                if should_mark_fraudulent(account_id):
                    merchant_stats[account_id]['is_fraudulent'] = True
                    fraudulent_merchants.add(account_id)

        elif operation == 'DISPUTE':
            charge_id = parts[1].strip()

            # Check if charge exists and was fraudulent
            if charge_id not in charge_registry:
                continue

            charge_info = charge_registry[charge_id]

            # Only process if currently marked as fraudulent
            if not charge_info['is_fraud_current']:
                continue

            # Update charge status to non-fraudulent
            charge_info['is_fraud_current'] = False

            # Update merchant fraud count
            account_id = charge_info['account_id']
            if account_id in merchant_stats:
                merchant_stats[account_id]['fraud_count'] -= 1

                # Check if merchant should have fraudulent status cleared
                if should_clear_fraudulent(account_id):
                    merchant_stats[account_id]['is_fraudulent'] = False
                    fraudulent_merchants.discard(account_id)

    # Return sorted list of fraudulent merchant IDs
    result = sorted(list(fraudulent_merchants))
    return ','.join(result) if result else ''


def run_test(name, non_fraud_codes, fraud_codes, mcc_thresholds, merchant_mcc_map, min_charges, charges, expected):
    """Helper function to run a test case."""
    result = find_fraudulent_merchants(non_fraud_codes, fraud_codes, mcc_thresholds, merchant_mcc_map, min_charges, charges)
    status = "✓" if result == expected else "✗"
    print(f"{status} {name}")
    if result != expected:
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
    return result == expected


# Global test counter
test_results = {"passed": 0, "failed": 0}

def test(name, non_fraud_codes, fraud_codes, mcc_thresholds, merchant_mcc_map, min_charges, charges, expected):
    """Wrapper to track test results."""
    passed = run_test(name, non_fraud_codes, fraud_codes, mcc_thresholds, merchant_mcc_map, min_charges, charges, expected)
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    return passed


if __name__ == '__main__':
    print("=" * 60)
    print("OFFICIAL TEST CASES")
    print("=" * 60)

    # Part 1: Count-based threshold
    print("\n[Part 1: Count-Based Thresholds]")
    test(
        "Part 1 Official",
        "approved,invalid_pin,expired_card",
        "do_not_honor,stolen_card,lost_card",
        ["retail,5", "airline,2", "restaurant,10"],
        ["acct_1,airline", "acct_2,venue", "acct_3,retail"],
        "3",
        [
            "CHARGE,ch_1,acct_1,100,do_not_honor",
            "CHARGE,ch_2,acct_1,200,approved",
            "CHARGE,ch_3,acct_1,300,do_not_honor",
            "CHARGE,ch_4,acct_2,100,lost_card",
            "CHARGE,ch_5,acct_2,200,lost_card",
            "CHARGE,ch_6,acct_2,300,lost_card",
            "CHARGE,ch_7,acct_3,100,lost_card",
            "CHARGE,ch_8,acct_2,800,stolen_card",
            "CHARGE,ch_9,acct_3,100,approved"
        ],
        "acct_1,acct_2"
    )

    # Part 2: Percentage-based threshold
    print("\n[Part 2: Percentage-Based Thresholds]")
    test(
        "Part 2 Official",
        "approved,invalid_pin,expired_card",
        "do_not_honor,stolen_card,lost_card",
        ["retail,0.5", "airline,0.25", "restaurant,0.8", "venue,0.25"],
        ["acct_1,airline", "acct_2,venue", "acct_3,venue"],
        "3",
        [
            "CHARGE,ch_1,acct_1,100,do_not_honor",
            "CHARGE,ch_2,acct_1,200,approved",
            "CHARGE,ch_3,acct_1,300,do_not_honor",
            "CHARGE,ch_4,acct_2,400,approved",
            "CHARGE,ch_5,acct_2,500,approved",
            "CHARGE,ch_6,acct_1,600,lost_card",
            "CHARGE,ch_7,acct_2,700,approved",
            "CHARGE,ch_8,acct_2,800,approved",
            "CHARGE,ch_9,acct_3,800,approved",
            "CHARGE,ch_10,acct_3,700,approved",
            "CHARGE,ch_11,acct_3,600,approved",
            "CHARGE,ch_12,acct_3,500,stolen_card",
            "CHARGE,ch_13,acct_3,500,stolen_card",
            "CHARGE,ch_14,acct_2,400,stolen_card"
        ],
        "acct_1,acct_3"
    )

    # Part 3: Dispute handling
    print("\n[Part 3: Dispute Handling]")
    test(
        "Part 3 Official",
        "approved,invalid_pin,expired_card",
        "do_not_honor,stolen_card,lost_card",
        ["retail,0.8", "venue,0.25"],
        ["acct_1,retail", "acct_2,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,do_not_honor",
            "CHARGE,ch_2,acct_1,200,lost_card",
            "CHARGE,ch_3,acct_1,300,do_not_honor",
            "DISPUTE,ch_2",
            "CHARGE,ch_4,acct_2,400,lost_card",
            "CHARGE,ch_5,acct_2,500,lost_card",
            "CHARGE,ch_6,acct_1,600,lost_card",
            "CHARGE,ch_7,acct_2,700,lost_card",
            "CHARGE,ch_8,acct_2,800,do_not_honor"
        ],
        "acct_2"
    )

    print("\n" + "=" * 60)
    print("EDGE CASE TESTS")
    print("=" * 60)

    # Edge Case 1: No transactions
    print("\n[Edge Cases: Basic]")
    test(
        "No transactions",
        "approved",
        "fraud",
        ["retail,1"],
        ["acct_1,retail"],
        "1",
        [],
        ""
    )

    # Edge Case 2: Below minimum transaction count
    test(
        "Below minimum count",
        "approved",
        "fraud",
        ["retail,1"],
        ["acct_1,retail"],
        "5",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,fraud",
            "CHARGE,ch_3,acct_1,100,fraud"
        ],
        ""
    )

    # Edge Case 3: Exactly at threshold (should mark)
    test(
        "Exact count threshold",
        "approved",
        "fraud",
        ["retail,2"],
        ["acct_1,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,fraud"
        ],
        "acct_1"
    )

    # Edge Case 4: Exactly at percentage threshold (should mark)
    test(
        "Exact percentage threshold",
        "approved",
        "fraud",
        ["retail,0.5"],
        ["acct_1,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,approved"
        ],
        "acct_1"
    )

    # Edge Case 5: Just below threshold (should not mark)
    test(
        "Below percentage threshold",
        "approved",
        "fraud",
        ["retail,0.5"],
        ["acct_1,retail"],
        "3",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,approved",
            "CHARGE,ch_3,acct_1,100,approved"
        ],
        ""
    )

    # Edge Case 6: Dispute non-existent charge
    print("\n[Edge Cases: Disputes]")
    test(
        "Dispute non-existent charge",
        "approved",
        "fraud",
        ["retail,0.5"],
        ["acct_1,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,fraud",
            "DISPUTE,ch_999"
        ],
        "acct_1"
    )

    # Edge Case 7: Dispute non-fraudulent charge
    test(
        "Dispute non-fraudulent charge",
        "approved",
        "fraud",
        ["retail,0.5"],
        ["acct_1,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,approved",
            "CHARGE,ch_2,acct_1,100,fraud",
            "DISPUTE,ch_1"
        ],
        "acct_1"
    )

    # Edge Case 8: Multiple disputes of same charge
    test(
        "Multiple disputes same charge",
        "approved",
        "fraud",
        ["retail,0.5"],
        ["acct_1,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,approved",
            "DISPUTE,ch_1",
            "DISPUTE,ch_1"
        ],
        ""
    )

    # Edge Case 9: Dispute before charge
    test(
        "Dispute before charge",
        "approved",
        "fraud",
        ["retail,0.5"],
        ["acct_1,retail"],
        "2",
        [
            "DISPUTE,ch_1",
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,fraud"
        ],
        "acct_1"
    )

    # Edge Case 10: Merchant not in MCC map
    print("\n[Edge Cases: Configuration]")
    test(
        "Merchant not in MCC map",
        "approved",
        "fraud",
        ["retail,1"],
        ["acct_1,retail"],
        "1",
        [
            "CHARGE,ch_1,acct_2,100,fraud"
        ],
        ""
    )

    # Edge Case 11: Zero threshold percentage
    test(
        "Zero threshold (any fraud marks)",
        "approved",
        "fraud",
        ["retail,0"],
        ["acct_1,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,approved",
            "CHARGE,ch_2,acct_1,100,fraud"
        ],
        "acct_1"
    )

    # Edge Case 12: 100% fraud ratio
    test(
        "All fraudulent transactions",
        "approved",
        "fraud",
        ["retail,0.5"],
        ["acct_1,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,fraud",
            "CHARGE,ch_3,acct_1,100,fraud"
        ],
        "acct_1"
    )

    # Edge Case 13: Sticky fraudulent status (stays fraudulent even when ratio drops)
    print("\n[Edge Cases: Sticky Status]")
    test(
        "Sticky status (ratio drops but stays fraudulent)",
        "approved",
        "fraud",
        ["retail,0.5"],
        ["acct_1,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,fraud",  # 2/2 = 1.0 >= 0.5 → MARKED
            "CHARGE,ch_3,acct_1,100,approved",  # 2/3 = 0.66 (still marked)
            "CHARGE,ch_4,acct_1,100,approved",  # 2/4 = 0.5 (still marked)
            "CHARGE,ch_5,acct_1,100,approved",  # 2/5 = 0.4 (still marked)
        ],
        "acct_1"
    )

    # Edge Case 14: Re-marking after dispute clears status
    test(
        "Re-mark after dispute clears",
        "approved",
        "fraud",
        ["retail,0.5"],
        ["acct_1,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,fraud",  # 2/2 = 1.0 → MARKED
            "DISPUTE,ch_1",  # 1/2 = 0.5 (still marked, exactly at threshold)
            "DISPUTE,ch_2",  # 0/2 = 0 → CLEARED
            "CHARGE,ch_3,acct_1,100,fraud",  # 1/3 = 0.33 (not marked)
            "CHARGE,ch_4,acct_1,100,fraud",  # 2/4 = 0.5 → RE-MARKED
        ],
        "acct_1"
    )

    # Edge Case 15: Multiple merchants mixed
    print("\n[Edge Cases: Multiple Merchants]")
    test(
        "Multiple merchants mixed modes",
        "approved",
        "fraud",
        ["retail,2", "airline,3"],
        ["acct_1,retail", "acct_2,airline", "acct_3,retail"],
        "3",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_2,100,fraud",
            "CHARGE,ch_3,acct_3,100,approved",
            "CHARGE,ch_4,acct_1,100,fraud",
            "CHARGE,ch_5,acct_2,100,fraud",
            "CHARGE,ch_6,acct_3,100,approved",
            "CHARGE,ch_7,acct_1,100,approved",  # acct_1: 2 frauds → MARKED
            "CHARGE,ch_8,acct_2,100,fraud",  # acct_2: 3 frauds → MARKED
            "CHARGE,ch_9,acct_3,100,approved",  # acct_3: 0 frauds
        ],
        "acct_1,acct_2"
    )

    # Edge Case 16: Empty code lists
    print("\n[Edge Cases: Empty/Invalid Inputs]")
    test(
        "Empty fraud codes",
        "approved",
        "",
        ["retail,1"],
        ["acct_1,retail"],
        "1",
        [
            "CHARGE,ch_1,acct_1,100,approved"
        ],
        ""
    )

    # Edge Case 17: Unknown code (not in either list)
    test(
        "Unknown transaction code",
        "approved",
        "fraud",
        ["retail,0.5"],
        ["acct_1,retail"],
        "2",
        [
            "CHARGE,ch_1,acct_1,100,unknown_code",
            "CHARGE,ch_2,acct_1,100,approved"
        ],
        ""
    )

    # Edge Case 18: Very large numbers
    print("\n[Edge Cases: Boundary Values]")
    test(
        "Large transaction counts",
        "approved",
        "fraud",
        ["retail,50"],
        ["acct_1,retail"],
        "100",
        [f"CHARGE,ch_{i},acct_1,100,fraud" for i in range(1, 51)] +
        [f"CHARGE,ch_{i},acct_1,100,approved" for i in range(51, 101)],
        "acct_1"
    )

    # Edge Case 19: Minimum charges = 1
    test(
        "Minimum charges = 1",
        "approved",
        "fraud",
        ["retail,1"],
        ["acct_1,retail"],
        "1",
        [
            "CHARGE,ch_1,acct_1,100,fraud"
        ],
        "acct_1"
    )

    # Edge Case 20: Complex dispute scenario
    print("\n[Edge Cases: Complex Scenarios]")
    test(
        "Complex dispute scenario",
        "approved",
        "fraud",
        ["retail,0.6"],
        ["acct_1,retail"],
        "3",
        [
            "CHARGE,ch_1,acct_1,100,fraud",
            "CHARGE,ch_2,acct_1,100,fraud",
            "CHARGE,ch_3,acct_1,100,fraud",  # 3/3 = 1.0 → MARKED
            "DISPUTE,ch_1",  # 2/3 = 0.66 (still marked)
            "DISPUTE,ch_2",  # 1/3 = 0.33 → CLEARED
            "CHARGE,ch_4,acct_1,100,approved",  # 1/4 = 0.25
            "CHARGE,ch_5,acct_1,100,fraud",  # 2/5 = 0.4
            "CHARGE,ch_6,acct_1,100,fraud",  # 3/6 = 0.5
            "CHARGE,ch_7,acct_1,100,fraud",  # 4/7 = 0.57
            "CHARGE,ch_8,acct_1,100,fraud",  # 5/8 = 0.625 → RE-MARKED
        ],
        "acct_1"
    )

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    total = test_results["passed"] + test_results["failed"]
    print(f"Total Tests: {total}")
    print(f"Passed: {test_results['passed']} ✓")
    print(f"Failed: {test_results['failed']} ✗")
    if test_results["failed"] == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {test_results['failed']} test(s) failed")
    print("=" * 60)
