"""
Stage 3: AI Extraction
======================

Extracts structured data from validated soldier lines using OpenAI API.

Features:
    - Retry with exponential backoff for API errors
    - Checkpoint/resume for interrupted runs
    - Parallel processing with configurable workers
    - Field validation after extraction
    - Source position tracking
    - Structured logging

Usage:
    python pipeline/03_ai_extract.py --workspace brigade_name
    python pipeline/03_ai_extract.py --workspace brigade_name --parallel 3 --resume

Input:  pipeline/workspaces/{workspace}/02_validated_lines.xlsx
Output: pipeline/workspaces/{workspace}/03_extracted_data.xlsx
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import argparse
import json
import os
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from openai import OpenAI

from utils.logging_config import setup_logging
from utils.retry import retry_with_backoff
from utils.checkpoint import CheckpointManager
from utils.validation import FieldValidator
from utils.parallel import ParallelExtractor

BATCH_SIZE = 30  # Soldiers per API call
API_KEY_FILE = Path("01-data/openai-api.txt")
PROMPT_FILE = Path("pipeline/prompts/extract_prompt.txt")


def load_api_key():
    """Load OpenAI API key from env var or file fallback."""
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key

    if not API_KEY_FILE.exists():
        raise FileNotFoundError(f"Set OPENAI_API_KEY env var or create {API_KEY_FILE}")

    content = API_KEY_FILE.read_text().strip()
    if content.startswith('OPENAI_API_KEY='):
        return content.split('=', 1)[1]
    return content


def load_prompt():
    """Load extraction prompt."""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding='utf-8')


class SoldierExtractor:
    """
    Main extraction engine with retry, validation, and error tracking.
    """

    def __init__(
        self,
        client: OpenAI,
        prompt: str,
        validator: FieldValidator,
        logger,
        max_retries: int = 5
    ):
        self.client = client
        self.prompt = prompt
        self.validator = validator
        self.logger = logger
        self.max_retries = max_retries

    def extract_batch(self, lines_batch: list, batch_index: int) -> dict:
        """
        Extract structured data from a batch of lines.

        Args:
            lines_batch: List of raw soldier lines
            batch_index: Index of this batch (for tracking)

        Returns:
            Dict with 'soldiers' list and 'tokens' count
        """
        return self._extract_with_retry(lines_batch, batch_index)

    @retry_with_backoff(max_retries=5, base_delay=2.0, max_delay=60.0)
    def _extract_with_retry(self, lines_batch: list, batch_index: int) -> dict:
        """API call with retry logic."""

        # Build input with explicit indices for tracking
        batch_text = ""
        for i, line in enumerate(lines_batch):
            batch_text += f"\n--- Soldier {i} ---\n{line}\n"

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": f"Extract data for these {len(lines_batch)} soldiers:\n{batch_text}"}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        soldiers = result.get('soldiers', [])

        # Track which input lines got results
        returned_count = len(soldiers)
        expected_count = len(lines_batch)

        if returned_count < expected_count:
            self.logger.warning(
                f"Batch {batch_index}: API returned {returned_count}/{expected_count} soldiers"
            )
            # Add placeholder entries for missing soldiers
            soldiers = self._fill_missing_soldiers(
                soldiers, lines_batch, batch_index
            )

        # Validate each soldier
        validated_soldiers = []
        for soldier in soldiers:
            validated = self.validator.validate(soldier)
            validated_soldiers.append(validated)

        return {
            'soldiers': validated_soldiers,
            'tokens': response.usage.total_tokens
        }

    def _fill_missing_soldiers(
        self,
        soldiers: list,
        lines_batch: list,
        batch_index: int
    ) -> list:
        """
        Fill in missing soldiers when API returns fewer than expected.

        Uses soldier indices if available, otherwise marks all extras as missing.
        """
        expected_count = len(lines_batch)
        result = [None] * expected_count

        # Try to match soldiers to their indices
        for soldier in soldiers:
            # Check if AI included an index field
            idx = soldier.get('_index')
            if idx is not None and 0 <= idx < expected_count:
                result[idx] = soldier
            else:
                # Find first empty slot
                for i in range(expected_count):
                    if result[i] is None:
                        result[i] = soldier
                        break

        # Fill remaining gaps with error placeholders
        for i in range(expected_count):
            if result[i] is None:
                self.logger.debug(
                    f"Batch {batch_index}, index {i}: No extraction result"
                )
                result[i] = {
                    'last_name': '',
                    'first_name': '',
                    'fathers_name': '',
                    'nickname': '',
                    'birth_year': '',
                    'birthplace': '',
                    'military_unit': '',
                    'rank_or_role': '',
                    'death_date': '',
                    'death_place': '',
                    'death_cause': '',
                    'other_info': '',
                    'confidence': 'low',
                    'parsing_issues': ['API returned no data for this line'],
                }

        return result


def process_extraction(args, workspace: Path, logger):
    """Main extraction processing."""

    input_file = workspace / "02_validated_lines.xlsx"
    output_file = workspace / "03_extracted_data.xlsx"
    checkpoint_file = workspace / "03_checkpoint.json"

    # Check input
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Run Stage 2 (validation) first.")
        return

    # Load data
    df = pd.read_excel(input_file)

    # Filter to valid lines only
    if args.valid_only:
        df = df[df['is_valid'] == 'yes']
        logger.info(f"Processing valid lines only: {len(df)}")
    else:
        logger.info(f"Processing all lines: {len(df)}")

    lines = df['raw_line'].tolist()
    total_lines = len(lines)

    if total_lines == 0:
        logger.warning("No lines to process!")
        return

    logger.info(f"Workspace: {args.workspace}")
    logger.info(f"Input: {input_file}")
    logger.info(f"Soldiers to extract: {total_lines}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Parallel workers: {args.parallel}")

    # Setup components
    client = OpenAI(api_key=load_api_key())
    prompt = load_prompt()
    validator = FieldValidator(logger=logger)
    checkpoint = CheckpointManager(checkpoint_file, logger=logger)

    extractor = SoldierExtractor(
        client=client,
        prompt=prompt,
        validator=validator,
        logger=logger,
        max_retries=args.max_retries
    )

    # Check for resume
    results = []
    total_tokens = 0
    confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
    start_batch = 0
    source_positions = []  # Track original line indices

    if args.resume and checkpoint.exists():
        resume_info = checkpoint.get_resume_info()
        logger.info(f"Resuming from checkpoint:\n{resume_info}")

        state = checkpoint.load()
        if state:
            start_batch = state['last_completed_batch'] + 1
            results = state['results']
            total_tokens = state['total_tokens']
            confidence_counts = state['confidence_counts']
            source_positions = state.get('source_positions', list(range(len(results))))
            logger.info(f"Resuming from batch {start_batch}")
    elif checkpoint.exists():
        logger.warning(
            "Checkpoint exists but --resume not specified. "
            "Starting fresh (checkpoint will be overwritten)."
        )

    # Create batches
    batches = []
    batch_positions = []  # Track source positions for each batch
    for i in range(0, total_lines, args.batch_size):
        batches.append(lines[i:i + args.batch_size])
        batch_positions.append(list(range(i, min(i + args.batch_size, total_lines))))

    total_batches = len(batches)
    logger.info(f"Total batches: {total_batches}, starting from: {start_batch}")

    start_time = time.time()

    # Progress callback
    def on_progress(completed, total, tokens):
        pct = completed / total * 100 if total > 0 else 0
        elapsed = time.time() - start_time
        rate = completed / elapsed if elapsed > 0 else 0
        remaining = total - completed
        eta = remaining / rate if rate > 0 else 0
        logger.info(
            f"Progress: {completed}/{total} batches ({pct:.1f}%) | "
            f"Tokens: {tokens:,} | ETA: {eta:.0f}s"
        )

    # Process batches
    if args.parallel > 1:
        # Parallel processing
        parallel = ParallelExtractor(
            extract_fn=extractor.extract_batch,
            workers=args.parallel,
            rate_limit_delay=0.3,
            logger=logger
        )

        result = parallel.process_batches(
            batches,
            start_batch=start_batch,
            progress_callback=on_progress
        )

        # Collect results in order
        for batch_idx in range(start_batch, total_batches):
            if batch_idx in result['results']:
                batch_result = result['results'][batch_idx]
                batch_lines = batches[batch_idx]
                positions = batch_positions[batch_idx]

                for j, soldier in enumerate(batch_result.get('soldiers', [])):
                    if j < len(batch_lines):
                        # Update stats
                        conf = soldier.get('confidence', 'medium')
                        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

                        # Convert parsing_issues to string if list
                        issues = soldier.get('parsing_issues', [])
                        if isinstance(issues, list):
                            issues = ', '.join(issues)

                        results.append({
                            'source_position': positions[j],
                            'raw_line': batch_lines[j],
                            'last_name': soldier.get('last_name', ''),
                            'first_name': soldier.get('first_name', ''),
                            'fathers_name': soldier.get('fathers_name', ''),
                            'nickname': soldier.get('nickname', ''),
                            'birth_year': soldier.get('birth_year', ''),
                            'birthplace': soldier.get('birthplace', ''),
                            'military_unit': soldier.get('military_unit', ''),
                            'rank_or_role': soldier.get('rank_or_role', ''),
                            'death_date': soldier.get('death_date', ''),
                            'death_place': soldier.get('death_place', ''),
                            'death_cause': soldier.get('death_cause', ''),
                            'other_info': soldier.get('other_info', ''),
                            'confidence': conf,
                            'parsing_issues': issues,
                        })
                        source_positions.append(positions[j])

            elif batch_idx in result['errors']:
                # Handle batch errors
                batch_lines = batches[batch_idx]
                positions = batch_positions[batch_idx]
                error = result['errors'][batch_idx]

                for j, line in enumerate(batch_lines):
                    confidence_counts['low'] = confidence_counts.get('low', 0) + 1
                    results.append({
                        'source_position': positions[j],
                        'raw_line': line,
                        'last_name': '',
                        'first_name': '',
                        'fathers_name': '',
                        'nickname': '',
                        'birth_year': '',
                        'birthplace': '',
                        'military_unit': '',
                        'rank_or_role': '',
                        'death_date': '',
                        'death_place': '',
                        'death_cause': '',
                        'other_info': '',
                        'confidence': 'low',
                        'parsing_issues': f'Batch error: {str(error)}',
                    })
                    source_positions.append(positions[j])

        total_tokens += result['total_tokens']

    else:
        # Sequential processing
        for batch_idx in range(start_batch, total_batches):
            batch = batches[batch_idx]
            positions = batch_positions[batch_idx]

            try:
                result = extractor.extract_batch(batch, batch_idx)
                total_tokens += result['tokens']

                # Map results back to lines
                for j, soldier in enumerate(result['soldiers']):
                    if j < len(batch):
                        conf = soldier.get('confidence', 'medium')
                        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

                        issues = soldier.get('parsing_issues', [])
                        if isinstance(issues, list):
                            issues = ', '.join(issues)

                        results.append({
                            'source_position': positions[j],
                            'raw_line': batch[j],
                            'last_name': soldier.get('last_name', ''),
                            'first_name': soldier.get('first_name', ''),
                            'fathers_name': soldier.get('fathers_name', ''),
                            'nickname': soldier.get('nickname', ''),
                            'birth_year': soldier.get('birth_year', ''),
                            'birthplace': soldier.get('birthplace', ''),
                            'military_unit': soldier.get('military_unit', ''),
                            'rank_or_role': soldier.get('rank_or_role', ''),
                            'death_date': soldier.get('death_date', ''),
                            'death_place': soldier.get('death_place', ''),
                            'death_cause': soldier.get('death_cause', ''),
                            'other_info': soldier.get('other_info', ''),
                            'confidence': conf,
                            'parsing_issues': issues,
                        })
                        source_positions.append(positions[j])

                # Progress
                on_progress(batch_idx - start_batch + 1, total_batches - start_batch, total_tokens)

                # Save checkpoint after each batch
                checkpoint.save(
                    last_completed_batch=batch_idx,
                    results=results,
                    total_tokens=total_tokens,
                    confidence_counts=confidence_counts,
                    source_file=str(input_file),
                    extra_data={'source_positions': source_positions}
                )

            except Exception as e:
                logger.error(f"Error in batch {batch_idx}: {e}")
                # Add failed lines with error marker
                for j, line in enumerate(batch):
                    confidence_counts['low'] = confidence_counts.get('low', 0) + 1
                    results.append({
                        'source_position': positions[j],
                        'raw_line': line,
                        'last_name': '',
                        'first_name': '',
                        'fathers_name': '',
                        'nickname': '',
                        'birth_year': '',
                        'birthplace': '',
                        'military_unit': '',
                        'rank_or_role': '',
                        'death_date': '',
                        'death_place': '',
                        'death_cause': '',
                        'other_info': '',
                        'confidence': 'low',
                        'parsing_issues': f'API error: {str(e)}',
                    })
                    source_positions.append(positions[j])

                # Save checkpoint even on error
                checkpoint.save(
                    last_completed_batch=batch_idx,
                    results=results,
                    total_tokens=total_tokens,
                    confidence_counts=confidence_counts,
                    source_file=str(input_file),
                    extra_data={'source_positions': source_positions}
                )

    # Save results
    result_df = pd.DataFrame(results)
    result_df.to_excel(output_file, index=False)

    # Clear checkpoint on success
    checkpoint.clear()

    # Calculate cost
    elapsed = time.time() - start_time
    input_tokens = total_tokens * 0.7
    output_tokens = total_tokens * 0.3
    cost = (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)

    # Get validation stats
    val_stats = validator.get_stats()
    issues_count = len([r for r in results if r.get('parsing_issues')])

    logger.info("=" * 60)
    logger.info("EXTRACTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total extracted: {len(results)}")
    logger.info(f"Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    logger.info(f"Tokens: {total_tokens:,}")
    logger.info(f"Est. cost: ${cost:.3f}")
    logger.info("")
    logger.info("Confidence breakdown:")
    logger.info(f"  High:   {confidence_counts.get('high', 0)}")
    logger.info(f"  Medium: {confidence_counts.get('medium', 0)}")
    logger.info(f"  Low:    {confidence_counts.get('low', 0)}")
    logger.info(f"  With issues: {issues_count}")
    logger.info("")
    logger.info("Validation stats:")
    logger.info(f"  Validated: {val_stats['validated']}")
    logger.info(f"  Issues added: {val_stats['issues_added']}")
    logger.info(f"  Confidence downgraded: {val_stats['confidence_downgraded']}")
    logger.info("")
    logger.info(f"Output: {output_file}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Review extracted data in Excel")
    logger.info("2. Check rows with confidence=low or parsing_issues")
    logger.info(f"3. Run: python pipeline/04_import_to_db.py --workspace {args.workspace} --brigade-code X")


def main():
    parser = argparse.ArgumentParser(description='Stage 3: AI Extraction')
    parser.add_argument('--workspace', required=True, help='Workspace folder name')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Soldiers per batch')
    parser.add_argument('--valid-only', action='store_true', default=True,
                        help='Only process valid lines (default: True)')
    parser.add_argument('--parallel', type=int, default=1,
                        help='Number of parallel workers (1-5, default: 1)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from checkpoint if available')
    parser.add_argument('--max-retries', type=int, default=5,
                        help='Max API retry attempts (default: 5)')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING'],
                        help='Logging level (default: INFO)')
    args = parser.parse_args()

    workspace = Path(f"pipeline/workspaces/{args.workspace}")

    # Setup logging
    logger = setup_logging(
        log_file='03_extract.log',
        log_level=args.log_level,
        workspace=workspace
    )

    logger.info("=" * 60)
    logger.info("STAGE 3: AI EXTRACTION")
    logger.info("=" * 60)

    try:
        process_extraction(args, workspace, logger)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user. Progress saved to checkpoint.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
