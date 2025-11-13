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
    - Part 2: Percentage-based thresholds (decimal thresholds)
    - Part 3: Dispute handling
    """
    # Parse non-fraud and fraud codes
    non_fraud_set = set(code.strip() for code in non_fraud_codes.split(',') if code.strip())
    fraud_set = set(code.strip() for code in fraud_codes.split(',') if code.strip())

    # Parse MCC thresholds
    mcc_threshold_map = {}
    for row in mcc_thresholds:
        if not row.strip():
            continue
        parts = row.split(',')
        mcc = parts[0].strip()
        threshold = parts[1].strip()
        # Determine if it's a percentage (float) or count (int)
        if '.' in threshold:
            mcc_threshold_map[mcc] = float(threshold)
        else:
            mcc_threshold_map[mcc] = int(threshold)

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

    # Determine if we're using percentage-based thresholds
    is_percentage_mode = any(isinstance(v, float) for v in mcc_threshold_map.values())

    # Track merchant data
    merchant_data = {}
    fraudulent_merchants = set()

    # Track charge details for dispute handling
    charge_details = {}

    # Process charges and disputes
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

            # Initialize merchant data if needed
            if account_id not in merchant_data:
                merchant_data[account_id] = {
                    'total_count': 0,
                    'fraud_count': 0,
                    'is_fraudulent': False,
                    'charges': []
                }

            # Determine if charge is fraudulent
            is_fraud = code in fraud_set

            # Store charge details
            charge_details[charge_id] = {
                'account_id': account_id,
                'is_fraud': is_fraud,
                'code': code
            }

            # Update merchant data
            merchant_data[account_id]['total_count'] += 1
            if is_fraud:
                merchant_data[account_id]['fraud_count'] += 1
            merchant_data[account_id]['charges'].append(charge_id)

            # Check if merchant should be marked as fraudulent
            if account_id in merchant_mcc:
                mcc = merchant_mcc[account_id]

                # Get threshold for this MCC, use default if not found
                threshold = None
                if mcc in mcc_threshold_map:
                    threshold = mcc_threshold_map[mcc]
                elif not is_percentage_mode:
                    # For count-based mode, use default threshold of 1 for undefined MCCs
                    threshold = 1

                if threshold is not None:
                    total = merchant_data[account_id]['total_count']
                    fraud_count = merchant_data[account_id]['fraud_count']

                    # Only evaluate if we've seen enough transactions
                    if total >= min_charges_count:
                        if is_percentage_mode:
                            # Percentage-based threshold
                            fraud_ratio = fraud_count / total

                            # Once marked fraudulent, stays fraudulent
                            if not merchant_data[account_id]['is_fraudulent']:
                                if fraud_ratio >= threshold:
                                    merchant_data[account_id]['is_fraudulent'] = True
                                    fraudulent_merchants.add(account_id)
                            else:
                                # Already fraudulent, keep in set
                                fraudulent_merchants.add(account_id)
                        else:
                            # Count-based threshold
                            if fraud_count >= threshold:
                                merchant_data[account_id]['is_fraudulent'] = True
                                fraudulent_merchants.add(account_id)

        elif operation == 'DISPUTE':
            charge_id = parts[1].strip()

            # Check if charge exists
            if charge_id in charge_details:
                charge_info = charge_details[charge_id]
                account_id = charge_info['account_id']

                # Only process if the charge was fraudulent
                if charge_info['is_fraud']:
                    # Convert to non-fraudulent
                    charge_info['is_fraud'] = False

                    # Update merchant fraud count
                    if account_id in merchant_data:
                        merchant_data[account_id]['fraud_count'] -= 1

                        # Check if merchant should be cleared from fraudulent status
                        if merchant_data[account_id]['is_fraudulent']:
                            if account_id in merchant_mcc:
                                mcc = merchant_mcc[account_id]

                                # Get threshold for this MCC, use default if not found
                                threshold = None
                                if mcc in mcc_threshold_map:
                                    threshold = mcc_threshold_map[mcc]
                                elif not is_percentage_mode:
                                    # For count-based mode, use default threshold of 1 for undefined MCCs
                                    threshold = 1

                                if threshold is not None:
                                    total = merchant_data[account_id]['total_count']
                                    fraud_count = merchant_data[account_id]['fraud_count']

                                    if total >= min_charges_count:
                                        if is_percentage_mode:
                                            fraud_ratio = fraud_count / total if total > 0 else 0

                                            # Clear fraudulent status if below threshold
                                            if fraud_ratio < threshold:
                                                merchant_data[account_id]['is_fraudulent'] = False
                                                fraudulent_merchants.discard(account_id)
                                        else:
                                            # Count-based threshold
                                            if fraud_count < threshold:
                                                merchant_data[account_id]['is_fraudulent'] = False
                                                fraudulent_merchants.discard(account_id)

    # Return sorted list of fraudulent merchants
    result = sorted(list(fraudulent_merchants))
    return ','.join(result)


if __name__ == '__main__':
    # Example test case from Part 1
    print("Part 1 Example:")
    non_fraud_codes = "approved,invalid_pin,expired_card"
    fraud_codes = "do_not_honor,stolen_card,lost_card"
    mcc_thresholds = [
        "retail,5",
        "airline,2",
        "restaurant,10"
    ]
    merchant_mcc_map = [
        "acct_1,airline",
        "acct_2,venue",
        "acct_3,retail"
    ]
    min_charges = "3"
    charges = [
        "CHARGE,ch_1,acct_1,100,do_not_honor",
        "CHARGE,ch_2,acct_1,200,approved",
        "CHARGE,ch_3,acct_1,300,do_not_honor",
        "CHARGE,ch_4,acct_2,400,approved",
        "CHARGE,ch_5,acct_2,500,approved",
        "CHARGE,ch_6,acct_1,600,lost_card",
        "CHARGE,ch_7,acct_1,700,lost_card",
        "CHARGE,ch_8,acct_2,800,stolen_card",
        "CHARGE,ch_9,acct_3,100,approved"
    ]
    result = find_fraudulent_merchants(non_fraud_codes, fraud_codes, mcc_thresholds, merchant_mcc_map, min_charges, charges)
    print(f"Result: {result}")
    print(f"Expected: acct_1,acct_2")
    print()

    # Example test case from Part 2
    # NOTE: The problem statement appears to have a typo. The explanation mentions
    # "below the threshold of 0.25" for acct_2 (venue MCC), suggesting venue should
    # be 0.25, not 0. Using 0.25 makes the test case consistent with the expected output.
    print("Part 2 Example:")
    non_fraud_codes = "approved,invalid_pin,expired_card"
    fraud_codes = "do_not_honor,stolen_card,lost_card"
    mcc_thresholds = [
        "retail,0.5",
        "airline,0.25",
        "restaurant,0.8",
        "venue,0.25"  # Changed from 0 to 0.25 based on problem explanation
    ]
    merchant_mcc_map = [
        "acct_1,airline",
        "acct_2,venue",
        "acct_3,venue"
    ]
    min_charges = "3"
    charges = [
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
    ]
    result = find_fraudulent_merchants(non_fraud_codes, fraud_codes, mcc_thresholds, merchant_mcc_map, min_charges, charges)
    print(f"Result: {result}")
    print(f"Expected: acct_1,acct_3")
    print()

    # Example test case from Part 3
    print("Part 3 Example:")
    non_fraud_codes = "approved,invalid_pin,expired_card"
    fraud_codes = "do_not_honor,stolen_card,lost_card"
    mcc_thresholds = [
        "retail,0.8",
        "venue,0.25"
    ]
    merchant_mcc_map = [
        "acct_1,retail",
        "acct_2,retail"
    ]
    min_charges = "2"
    charges = [
        "CHARGE,ch_1,acct_1,100,do_not_honor",
        "CHARGE,ch_2,acct_1,200,lost_card",
        "CHARGE,ch_3,acct_1,300,do_not_honor",
        "DISPUTE,ch_2",
        "CHARGE,ch_4,acct_2,400,lost_card",
        "CHARGE,ch_5,acct_2,500,lost_card",
        "CHARGE,ch_6,acct_1,600,lost_card",
        "CHARGE,ch_7,acct_2,700,lost_card",
        "CHARGE,ch_8,acct_2,800,do_not_honor"
    ]
    result = find_fraudulent_merchants(non_fraud_codes, fraud_codes, mcc_thresholds, merchant_mcc_map, min_charges, charges)
    print(f"Result: {result}")
    print(f"Expected: acct_2")
