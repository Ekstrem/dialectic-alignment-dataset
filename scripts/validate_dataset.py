"""Validate DAD dataset structure and DPO pair consistency."""
import json
import sys

def validate(jsonl_path):
    errors = []
    with open(jsonl_path, 'r') as f:
        for i, line in enumerate(f, 1):
            try:
                record = json.loads(line)
                # Required fields
                for field in ['id', 'module', 'title', 'prompt', 'chosen', 'rejected', 'symptoms', 'metadata']:
                    if field not in record:
                        errors.append(f"Line {i}: missing required field '{field}'")
                # DPO pair non-empty
                if record.get('chosen', '') == '' or record.get('rejected', '') == '':
                    errors.append(f"Line {i}: empty chosen or rejected")
                # Module code valid
                valid_modules = ['00-context', '01-self-audit', '02-diagnostics', '03-hostile-reading', '04-toolkit']
                if record.get('module') not in valid_modules:
                    errors.append(f"Line {i}: invalid module '{record.get('module')}'")
            except json.JSONDecodeError as e:
                errors.append(f"Line {i}: invalid JSON - {e}")
    
    if errors:
        print(f"❌ Validation failed with {len(errors)} errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print(f"✅ Validated {i} records successfully.")

if __name__ == "__main__":
    validate("dataset/dialectic_alignment.jsonl")