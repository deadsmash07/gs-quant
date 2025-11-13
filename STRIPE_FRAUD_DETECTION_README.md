# Stripe Fraud Detection Model

A comprehensive fraud detection system for identifying fraudulent merchants based on transaction patterns.

## Overview

This implementation provides a fraud detection model that processes credit card transactions and identifies potentially fraudulent merchants using three progressively sophisticated approaches:

1. **Part 1: Count-Based Thresholds** - Simple fraud count threshold per MCC
2. **Part 2: Percentage-Based Thresholds** - Fraud ratio thresholds with persistence
3. **Part 3: Dispute Handling** - Dynamic status updates based on merchant disputes

## Features

### Part 1: Count-Based Detection
- Tracks fraudulent transaction counts per merchant
- Each Merchant Category Code (MCC) has a configurable fraud threshold
- Merchants with fraud counts at or above threshold are marked fraudulent
- Minimum transaction count required before evaluation
- Default threshold of 1 for undefined MCCs

### Part 2: Percentage-Based Detection
- Uses fraud percentage (fraud_count / total_count) instead of raw counts
- Once marked fraudulent, merchants remain fraudulent (sticky flag)
- More suitable for high-volume merchants (e.g., Amazon, Ticketmaster)
- Prevents false positives from early transaction patterns

### Part 3: Dispute Handling
- Merchants can dispute fraudulent transaction classifications
- Successful disputes convert fraud transactions to non-fraudulent
- Fraudulent status can be cleared if fraud ratio drops below threshold
- Merchants can be re-marked as fraudulent if they meet criteria again

## Implementation Details

### Key Algorithms

**Fraud Detection Logic:**
```python
if fraud_ratio >= threshold:
    mark_as_fraudulent()
```

**Dispute Processing:**
```python
if dispute_successful:
    fraud_count -= 1
    if fraud_ratio < threshold:
        clear_fraudulent_status()
```

### Edge Cases Handled

1. **Missing MCC Thresholds**: Count-based mode uses default threshold of 1
2. **Zero Division**: Handles edge case where total transactions is 0
3. **Sticky Fraudulent Status**: Part 2+ maintains fraudulent flag once set
4. **Minimum Transaction Count**: Only evaluates merchants after minimum transactions seen
5. **Sequential Processing**: All charges and disputes processed in chronological order

## Usage

```python
from stripe_fraud_detection import find_fraudulent_merchants

result = find_fraudulent_merchants(
    non_fraud_codes="approved,invalid_pin,expired_card",
    fraud_codes="do_not_honor,stolen_card,lost_card",
    mcc_thresholds=[
        "retail,5",
        "airline,2",
        "restaurant,10"
    ],
    merchant_mcc_map=[
        "acct_1,airline",
        "acct_2,retail"
    ],
    min_charges="3",
    charges=[
        "CHARGE,ch_1,acct_1,100,do_not_honor",
        "CHARGE,ch_2,acct_1,200,approved",
        "DISPUTE,ch_1"
    ]
)

print(result)  # Output: Comma-separated list of fraudulent merchant IDs
```

## Input Format

### Parameters

1. **non_fraud_codes**: Comma-separated list of non-fraudulent response codes
2. **fraud_codes**: Comma-separated list of fraudulent response codes
3. **mcc_thresholds**: Array of "mcc,threshold" pairs
   - Count mode: threshold is integer (e.g., "retail,5")
   - Percentage mode: threshold is decimal (e.g., "retail,0.5")
4. **merchant_mcc_map**: Array of "account_id,mcc" pairs
5. **min_charges**: Minimum transactions before evaluation (string integer)
6. **charges**: Array of charge/dispute records
   - Charge format: "CHARGE,charge_id,account_id,amount,code"
   - Dispute format: "DISPUTE,charge_id"

### Output

Comma-separated, lexicographically sorted list of fraudulent merchant account IDs.

Example: `"acct_1,acct_2,acct_5"`

## Test Cases

### Part 1: Count-Based
```
Input: 3 transactions minimum, airline threshold=2
acct_1 (airline): 4 frauds → FRAUDULENT ✓
acct_2 (venue): 1 fraud (default threshold=1) → FRAUDULENT ✓
acct_3 (retail): 0 frauds (threshold=5) → CLEAN ✓
```

### Part 2: Percentage-Based
```
Input: 3 transactions minimum
acct_1 (airline, 0.25): 66% fraud ratio → FRAUDULENT ✓
acct_2 (venue, 0.25): 20% fraud ratio → CLEAN ✓
acct_3 (venue, 0.25): 40% fraud ratio → FRAUDULENT ✓
```

### Part 3: With Disputes
```
Input: 2 transactions minimum
acct_1 (retail, 0.8): Marked fraudulent at ch_2 (100% ratio)
                      Dispute ch_2 → ratio drops to 66% → CLEARED
                      Additional fraud ch_6 → ratio 75% < 80% → CLEAN ✓
acct_2 (retail, 0.8): 100% fraud ratio maintained → FRAUDULENT ✓
```

## Technical Notes

### Mode Detection
The system automatically detects which mode to use based on threshold types:
- If any threshold contains a decimal point → Percentage mode
- Otherwise → Count mode

### Performance Characteristics
- **Time Complexity**: O(n) where n is number of charges/disputes
- **Space Complexity**: O(m) where m is number of merchants
- **Processing**: Sequential, order-dependent

### Known Issues

1. **Test Case Typo**: The original Part 2 example has `venue,0` which should be `venue,0.25` based on the problem explanation. The implementation includes both versions with documentation.

## Production Considerations

For deployment to production systems:

1. **Threshold Tuning**: Calibrate thresholds based on historical fraud data
2. **MCC Coverage**: Ensure all expected MCCs have defined thresholds
3. **Monitoring**: Track false positive/negative rates
4. **Performance**: Consider batch processing for large transaction volumes
5. **Audit Trail**: Log all fraud determinations for compliance
6. **Real-time**: This implementation is suitable for stream processing
7. **State Management**: Merchant state should be persisted for distributed systems

## License

This implementation is provided as a coding assessment solution.
