"""
Stage 2: AI Validation
======================

Validates that each line contains exactly one soldier entry.
Flags merged entries, incomplete lines, and garbage.

Usage:
    python pipeline/02_ai_validate.py --workspace brigade_name

Input:  pipeline/workspaces/{workspace}/01_raw_lines.xlsx
Output: pipeline/workspaces/{workspace}/02_validated_lines.xlsx
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import argparse
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from openai import OpenAI

BATCH_SIZE = 50  # Lines per API call
API_KEY_FILE = Path("01-data/openai-api.txt")

# Load prompt
PROMPT_FILE = Path("pipeline/prompts/validate_prompt.txt")


def load_api_key():
    """Load OpenAI API key."""
    if not API_KEY_FILE.exists():
        raise FileNotFoundError(f"API key file not found: {API_KEY_FILE}")

    content = API_KEY_FILE.read_text().strip()
    if content.startswith('OPENAI_API_KEY='):
        return content.split('=', 1)[1]
    return content


def load_prompt():
    """Load validation prompt."""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding='utf-8')


def validate_batch(client, prompt, lines_batch, start_index):
    """Validate a batch of lines with AI."""

    # Build numbered input
    batch_text = ""
    for i, line in enumerate(lines_batch):
        batch_text += f"{start_index + i + 1}. {line}\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Validate these {len(lines_batch)} lines:\n\n{batch_text}"}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    return {
        'validations': result.get('validations', []),
        'tokens': response.usage.total_tokens
    }


def main():
    parser = argparse.ArgumentParser(description='Stage 2: AI Validation')
    parser.add_argument('--workspace', required=True, help='Workspace folder name')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Lines per batch')
    args = parser.parse_args()

    workspace = Path(f"pipeline/workspaces/{args.workspace}")
    input_file = workspace / "01_raw_lines.xlsx"
    output_file = workspace / "02_validated_lines.xlsx"
    log_file = workspace / "processing.log"

    print("=" * 60)
    print("STAGE 2: AI VALIDATION")
    print("=" * 60)

    # Check input
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        print("Run Stage 1 (parser) first.")
        return

    # Load data
    df = pd.read_excel(input_file)
    lines = df['raw_line'].tolist()
    total_lines = len(lines)

    print(f"Workspace: {args.workspace}")
    print(f"Input: {input_file}")
    print(f"Lines to validate: {total_lines}")
    print(f"Batch size: {args.batch_size}")
    print()

    # Setup
    client = OpenAI(api_key=load_api_key())
    prompt = load_prompt()

    # Results storage
    results = []
    total_tokens = 0
    start_time = time.time()

    # Process batches
    batch_num = 0
    for i in range(0, total_lines, args.batch_size):
        batch_num += 1
        batch = lines[i:i + args.batch_size]

        try:
            result = validate_batch(client, prompt, batch, i)
            total_tokens += result['tokens']

            # Map results back to lines
            validation_map = {v['line_num']: v for v in result['validations']}

            for j, line in enumerate(batch):
                line_num = i + j + 1
                v = validation_map.get(line_num, {})
                results.append({
                    'raw_line': line,
                    'is_valid': 'yes' if v.get('is_valid', True) else 'no',
                    'issue_type': v.get('issue_type', ''),
                    'suggested_fix': v.get('suggested_fix', '')
                })

            # Progress
            processed = min(i + args.batch_size, total_lines)
            pct = processed / total_lines * 100
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total_lines - processed) / rate if rate > 0 else 0

            print(f"Batch {batch_num}: {processed}/{total_lines} ({pct:.1f}%) | "
                  f"Tokens: {total_tokens:,} | ETA: {eta:.0f}s")

        except Exception as e:
            print(f"ERROR in batch {batch_num}: {e}")
            # Add unprocessed lines as valid (safe default)
            for line in batch:
                results.append({
                    'raw_line': line,
                    'is_valid': 'yes',
                    'issue_type': 'error',
                    'suggested_fix': f'API error: {str(e)}'
                })
            time.sleep(2)

    # Save results
    result_df = pd.DataFrame(results)
    result_df.to_excel(output_file, index=False)

    # Stats
    valid_count = sum(1 for r in results if r['is_valid'] == 'yes')
    invalid_count = len(results) - valid_count

    elapsed = time.time() - start_time
    cost = total_tokens * 0.15 / 1_000_000 + total_tokens * 0.3 * 0.60 / 1_000_000

    print()
    print("=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print(f"Total lines: {len(results)}")
    print(f"Valid: {valid_count}")
    print(f"Issues found: {invalid_count}")
    print(f"Time: {elapsed:.1f}s")
    print(f"Tokens: {total_tokens:,}")
    print(f"Est. cost: ${cost:.3f}")
    print()
    print(f"Output: {output_file}")

    # Issue breakdown
    if invalid_count > 0:
        print("\nIssue breakdown:")
        issue_counts = result_df[result_df['is_valid'] == 'no']['issue_type'].value_counts()
        for issue, count in issue_counts.items():
            print(f"  {issue}: {count}")

    print()
    print("Next steps:")
    print("1. Review issues in Excel")
    print("2. Fix or remove invalid lines")
    print(f"3. Run: python pipeline/03_ai_extract.py --workspace {args.workspace}")

    # Log
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n[{datetime.now().isoformat()}] Stage 2: Validated {len(results)} lines, "
                f"{invalid_count} issues, {total_tokens} tokens\n")


if __name__ == "__main__":
    main()
