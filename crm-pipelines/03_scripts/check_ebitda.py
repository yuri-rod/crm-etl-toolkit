#!/usr/bin/env python3
"""Check EBITDA data in valuation JSON files"""

import json

# Load the valuation data
with open('valuation-20250826-1820.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total records: {len(data)}")
print("\nChecking EBITDA values in first 10 records...")
print("-" * 60)

for i, record in enumerate(data[:10]):
    # Check different possible field names
    ebitda1 = record.get('financials.currentPlannedEBITDA', 'NOT FOUND')
    
    # Check if financials is nested
    financials = record.get('financials', {})
    ebitda2 = financials.get('currentPlannedEBITDA', 'NOT FOUND') if isinstance(financials, dict) else 'NOT FOUND'
    
    company = record.get('overview.company', record.get('company', f'Record {i}'))
    
    print(f"Record {i}:")
    print(f"  Company: {company}")
    print(f"  financials.currentPlannedEBITDA (flat): {ebitda1}")
    print(f"  financials->currentPlannedEBITDA (nested): {ebitda2}")
    print()

# Count non-zero EBITDA values
ebitda_count = 0
ebitda_values = []

for record in data:
    # Try flat structure
    ebitda_val = record.get('financials.currentPlannedEBITDA', 0)
    if ebitda_val and ebitda_val != 0:
        ebitda_count += 1
        ebitda_values.append(ebitda_val)

print(f"\nRecords with non-zero EBITDA (flat structure): {ebitda_count}")
if ebitda_values:
    print(f"Sample EBITDA values: {ebitda_values[:5]}")

# Check nested structure
nested_count = 0
nested_values = []

for record in data:
    financials = record.get('financials', {})
    if isinstance(financials, dict):
        ebitda_val = financials.get('currentPlannedEBITDA', 0)
        if ebitda_val and ebitda_val != 0:
            nested_count += 1
            nested_values.append(ebitda_val)

print(f"\nRecords with non-zero EBITDA (nested structure): {nested_count}")
if nested_values:
    print(f"Sample EBITDA values: {nested_values[:5]}")

# Show all field keys from first record to understand structure
print("\n" + "="*60)
print("All fields in first record:")
if data:
    for key in sorted(data[0].keys()):
        value = data[0][key]
        if 'EBITDA' in key.upper():
            print(f"  ⭐ {key}: {value}")
        else:
            print(f"  {key}: {type(value).__name__}")
