"""
Stage 4: Import to Database
===========================

Imports extracted soldier data into the main database.

Features:
    - Duplicate detection with configurable handling
    - Transaction batching with savepoints for granular rollback
    - Source position tracking
    - Structured logging

Usage:
    python pipeline/04_import_to_db.py --workspace brigade_name --brigade-code 5
    python pipeline/04_import_to_db.py --workspace brigade_name --brigade-code 5 --skip-duplicates

Input:  pipeline/workspaces/{workspace}/03_extracted_data.xlsx
Output: Records in 01-data/soldiers.db
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import argparse
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional

from utils.logging_config import setup_logging

DATABASE_PATH = Path("01-data/soldiers.db")
DEFAULT_BATCH_SIZE = 100


class DuplicateDetector:
    """
    Detects duplicate soldiers by raw_data and name matching.

    Caches existing soldiers on startup for fast lookup.
    """

    def __init__(self, conn: sqlite3.Connection, brigade_code: int, logger):
        """
        Initialize detector and cache existing soldiers.

        Args:
            conn: Database connection
            brigade_code: Brigade code to check for duplicates
            logger: Logger instance
        """
        self.conn = conn
        self.brigade_code = brigade_code
        self.logger = logger

        # Cache for duplicate detection
        self._raw_data_cache: Set[str] = set()
        self._name_cache: Set[Tuple[str, str]] = set()

        self._load_cache()

    def _load_cache(self) -> None:
        """Load existing soldiers into cache."""
        cursor = self.conn.cursor()

        # Load raw_data values
        cursor.execute("""
            SELECT raw_data FROM soldiers
            WHERE brigade_code = ? AND raw_data IS NOT NULL AND raw_data != ''
        """, (self.brigade_code,))

        for row in cursor.fetchall():
            if row[0]:
                self._raw_data_cache.add(self._normalize(row[0]))

        # Load name combinations
        cursor.execute("""
            SELECT last_name, first_name FROM soldiers
            WHERE brigade_code = ?
        """, (self.brigade_code,))

        for row in cursor.fetchall():
            name_key = (
                self._normalize(row[0] or ''),
                self._normalize(row[1] or '')
            )
            if name_key[0] or name_key[1]:
                self._name_cache.add(name_key)

        self.logger.info(
            f"Duplicate cache loaded: {len(self._raw_data_cache)} raw entries, "
            f"{len(self._name_cache)} name entries"
        )

    def _normalize(self, value: str) -> str:
        """Normalize string for comparison."""
        if not value:
            return ''
        return value.strip().lower()

    def check_duplicate(
        self,
        raw_data: str,
        last_name: str,
        first_name: str
    ) -> Optional[str]:
        """
        Check if a soldier is a duplicate.

        Args:
            raw_data: Raw line from source
            last_name: Extracted last name
            first_name: Extracted first name

        Returns:
            Match type ('exact_raw', 'name_match') or None if not duplicate
        """
        # Check exact raw_data match
        if raw_data:
            normalized_raw = self._normalize(raw_data)
            if normalized_raw in self._raw_data_cache:
                return 'exact_raw'

        # Check name match
        name_key = (
            self._normalize(last_name or ''),
            self._normalize(first_name or '')
        )
        if name_key[0] and name_key[1] and name_key in self._name_cache:
            return 'name_match'

        return None

    def add_to_cache(
        self,
        raw_data: str,
        last_name: str,
        first_name: str
    ) -> None:
        """Add a newly imported soldier to cache."""
        if raw_data:
            self._raw_data_cache.add(self._normalize(raw_data))

        name_key = (
            self._normalize(last_name or ''),
            self._normalize(first_name or '')
        )
        if name_key[0] or name_key[1]:
            self._name_cache.add(name_key)


class BatchImporter:
    """
    Imports soldiers in batches with savepoint-based transaction control.

    Uses SQLite savepoints for granular rollback on batch failure.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        brigade_code: int,
        duplicate_detector: DuplicateDetector,
        logger,
        batch_size: int = DEFAULT_BATCH_SIZE,
        skip_duplicates: bool = False
    ):
        self.conn = conn
        self.brigade_code = brigade_code
        self.detector = duplicate_detector
        self.logger = logger
        self.batch_size = batch_size
        self.skip_duplicates = skip_duplicates

        # Statistics
        self.stats = {
            'imported': 0,
            'skipped_duplicate': 0,
            'failed': 0,
            'failed_rows': [],
        }

    def import_all(
        self,
        rows: List[Dict],
        start_sequence: int
    ) -> Dict:
        """
        Import all rows in batches.

        Args:
            rows: List of soldier row dicts
            start_sequence: Starting sequence number

        Returns:
            Statistics dict
        """
        total = len(rows)
        current_seq = start_sequence

        for batch_start in range(0, total, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total)
            batch = rows[batch_start:batch_end]

            self.logger.debug(
                f"Processing batch {batch_start // self.batch_size + 1}: "
                f"rows {batch_start}-{batch_end-1}"
            )

            try:
                current_seq = self._import_batch(batch, current_seq)
            except Exception as e:
                self.logger.error(f"Batch failed: {e}")
                # Try row-by-row to identify bad rows
                current_seq = self._import_row_by_row(batch, current_seq)

            # Progress every batch
            if (batch_end) % 500 == 0 or batch_end == total:
                self.logger.info(
                    f"Progress: {batch_end}/{total} | "
                    f"Imported: {self.stats['imported']} | "
                    f"Skipped: {self.stats['skipped_duplicate']} | "
                    f"Failed: {self.stats['failed']}"
                )

        return self.stats

    def _import_batch(
        self,
        batch: List[Dict],
        start_seq: int
    ) -> int:
        """
        Import a batch with savepoint for atomic rollback.

        Returns:
            Next sequence number
        """
        cursor = self.conn.cursor()
        savepoint_name = f"batch_{start_seq}"

        cursor.execute(f"SAVEPOINT {savepoint_name}")

        current_seq = start_seq

        try:
            for row in batch:
                result = self._import_single_row(row, current_seq, cursor)
                if result == 'imported':
                    current_seq += 1

            cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
            return current_seq

        except Exception as e:
            cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
            cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
            raise

    def _import_row_by_row(
        self,
        batch: List[Dict],
        start_seq: int
    ) -> int:
        """
        Import rows one by one to identify failures.

        Returns:
            Next sequence number
        """
        cursor = self.conn.cursor()
        current_seq = start_seq

        for row in batch:
            try:
                result = self._import_single_row(row, current_seq, cursor)
                self.conn.commit()
                if result == 'imported':
                    current_seq += 1

            except Exception as e:
                self.conn.rollback()
                self.stats['failed'] += 1
                self.stats['failed_rows'].append({
                    'row': row.get('raw_line', '')[:100],
                    'error': str(e)
                })
                self.logger.warning(
                    f"Row failed: {str(e)[:100]} - {row.get('last_name', '?')}"
                )

        return current_seq

    def _import_single_row(
        self,
        row: Dict,
        sequence: int,
        cursor: sqlite3.Cursor
    ) -> str:
        """
        Import a single row.

        Returns:
            'imported', 'skipped', or raises exception
        """
        raw_data = str(row.get('raw_line', ''))
        last_name = str(row.get('last_name', ''))
        first_name = str(row.get('first_name', ''))

        # Check for duplicates
        dup_type = self.detector.check_duplicate(raw_data, last_name, first_name)

        if dup_type:
            if self.skip_duplicates:
                self.stats['skipped_duplicate'] += 1
                self.logger.debug(
                    f"Skipping duplicate ({dup_type}): {last_name} {first_name}"
                )
                return 'skipped'
            else:
                raise ValueError(
                    f"Duplicate detected ({dup_type}): {last_name} {first_name}. "
                    f"Use --skip-duplicates to skip."
                )

        # Generate soldier ID
        soldier_id = self._generate_soldier_id(self.brigade_code, sequence)

        # Get source position
        source_position = row.get('source_position')
        if source_position is not None:
            try:
                source_position = int(source_position)
            except (ValueError, TypeError):
                source_position = None

        # Insert
        cursor.execute("""
            INSERT INTO soldiers (
                soldier_id, brigade_code, sequence_num, source_position, raw_data,
                last_name, middle_name, first_name, additional_info,
                ai_processed, ai_process_count, ai_confidence, ai_parsing_issues,
                ai_last_name, ai_first_name, ai_fathers_name, ai_nickname,
                ai_birth_year, ai_birthplace, ai_military_unit, ai_rank_or_role,
                ai_death_date, ai_death_place, ai_death_cause, ai_other_info,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            soldier_id,
            self.brigade_code,
            sequence,
            source_position,
            raw_data,
            last_name,
            str(row.get('fathers_name', '')),  # middle_name stores father's name
            first_name,
            '',  # additional_info
            1,  # ai_processed
            1,  # ai_process_count
            str(row.get('confidence', 'medium')),
            str(row.get('parsing_issues', '')),
            last_name,
            first_name,
            str(row.get('fathers_name', '')),
            str(row.get('nickname', '')),
            str(row.get('birth_year', '')),
            str(row.get('birthplace', '')),
            str(row.get('military_unit', '')),
            str(row.get('rank_or_role', '')),
            str(row.get('death_date', '')),
            str(row.get('death_place', '')),
            str(row.get('death_cause', '')),
            str(row.get('other_info', '')),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        # Add to cache
        self.detector.add_to_cache(raw_data, last_name, first_name)
        self.stats['imported'] += 1

        return 'imported'

    def _generate_soldier_id(self, brigade_code: int, sequence: int) -> str:
        """Generate 10-digit soldier ID: BBBBNNNNNN"""
        if not (1 <= brigade_code <= 9999):
            raise ValueError(f"Brigade code must be 1-9999, got {brigade_code}")
        if not (1 <= sequence <= 999999):
            raise ValueError(f"Sequence must be 1-999999, got {sequence}")
        return str(brigade_code * 1_000_000 + sequence)


def get_next_sequence(conn: sqlite3.Connection, brigade_code: int) -> int:
    """Get the next sequence number for a brigade."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(sequence_num) FROM soldiers WHERE brigade_code = ?
    """, (brigade_code,))
    result = cursor.fetchone()[0]
    return (result or 0) + 1


def get_or_create_brigade(
    conn: sqlite3.Connection,
    brigade_code: int,
    brigade_name: str,
    logger
) -> None:
    """Ensure brigade exists in database."""
    cursor = conn.cursor()

    # Check if exists
    cursor.execute("SELECT code FROM brigades WHERE code = ?", (brigade_code,))
    if cursor.fetchone():
        return

    # Create new brigade
    json_file = f"website/public/{brigade_name.lower().replace(' ', '_')}_soldiers.json"
    cursor.execute("""
        INSERT INTO brigades (code, name, short_name, json_file)
        VALUES (?, ?, ?, ?)
    """, (brigade_code, brigade_name, brigade_name.lower().replace(' ', '_'), json_file))
    conn.commit()
    logger.info(f"Created new brigade: {brigade_code} - {brigade_name}")


def main():
    parser = argparse.ArgumentParser(description='Stage 4: Import to Database')
    parser.add_argument('--workspace', required=True, help='Workspace folder name')
    parser.add_argument('--brigade-code', type=int, required=True, help='Brigade code (1-9999)')
    parser.add_argument('--brigade-name', help='Brigade name (if new brigade)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without importing')
    parser.add_argument('--skip-duplicates', action='store_true',
                        help='Skip duplicate records instead of failing')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                        help=f'Records per transaction batch (default: {DEFAULT_BATCH_SIZE})')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING'],
                        help='Logging level (default: INFO)')
    args = parser.parse_args()

    workspace = Path(f"pipeline/workspaces/{args.workspace}")
    input_file = workspace / "03_extracted_data.xlsx"

    # Setup logging
    logger = setup_logging(
        log_file='04_import.log',
        log_level=args.log_level,
        workspace=workspace
    )

    logger.info("=" * 60)
    logger.info("STAGE 4: DATABASE IMPORT")
    logger.info("=" * 60)

    # Check input
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Run Stage 3 (extraction) first.")
        return

    if not DATABASE_PATH.exists():
        logger.error(f"Database not found: {DATABASE_PATH}")
        logger.error("Run scripts/setup_database.py first.")
        return

    # Load data
    df = pd.read_excel(input_file)
    rows = df.to_dict('records')
    total_soldiers = len(rows)

    logger.info(f"Workspace: {args.workspace}")
    logger.info(f"Brigade code: {args.brigade_code}")
    logger.info(f"Soldiers to import: {total_soldiers}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Skip duplicates: {args.skip_duplicates}")

    if args.dry_run:
        logger.info("*** DRY RUN - No changes will be made ***")

    # Preview data
    logger.info("")
    logger.info("Preview (first 5 rows):")
    preview_cols = ['last_name', 'first_name', 'fathers_name', 'confidence']
    logger.info(df[preview_cols].head().to_string())

    # Stats
    logger.info("")
    logger.info("Confidence distribution:")
    for conf, count in df['confidence'].value_counts().items():
        logger.info(f"  {conf}: {count}")

    low_confidence = len(df[df['confidence'] == 'low'])
    has_issues = len(df[df['parsing_issues'].notna() & (df['parsing_issues'] != '')])

    if low_confidence > 0:
        logger.warning(f"{low_confidence} soldiers with low confidence")
    if has_issues > 0:
        logger.warning(f"{has_issues} soldiers with parsing issues")

    if args.dry_run:
        logger.info("")
        logger.info("Dry run complete. To import for real, remove --dry-run flag.")
        return

    # Confirm
    print()
    confirm = input(f"Import {total_soldiers} soldiers to brigade {args.brigade_code}? (yes/no): ")
    if confirm.lower() != 'yes':
        logger.info("Cancelled by user.")
        return

    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Ensure brigade exists
        brigade_name = args.brigade_name or args.workspace.replace('_', ' ').title()
        get_or_create_brigade(conn, args.brigade_code, brigade_name, logger)

        # Get starting sequence
        next_seq = get_next_sequence(conn, args.brigade_code)
        logger.info(f"Starting sequence: {next_seq}")

        # Setup importer
        detector = DuplicateDetector(conn, args.brigade_code, logger)
        importer = BatchImporter(
            conn=conn,
            brigade_code=args.brigade_code,
            duplicate_detector=detector,
            logger=logger,
            batch_size=args.batch_size,
            skip_duplicates=args.skip_duplicates
        )

        # Import
        stats = importer.import_all(rows, next_seq)

        # Final commit
        conn.commit()

        # Report results
        logger.info("")
        logger.info("=" * 60)
        logger.info("IMPORT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Imported: {stats['imported']}")
        logger.info(f"Skipped (duplicates): {stats['skipped_duplicate']}")
        logger.info(f"Failed: {stats['failed']}")

        if stats['failed_rows']:
            logger.info("")
            logger.info("Failed rows:")
            for fail in stats['failed_rows'][:10]:
                logger.info(f"  - {fail['error'][:80]}")
            if len(stats['failed_rows']) > 10:
                logger.info(f"  ... and {len(stats['failed_rows']) - 10} more")

        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Run: python scripts/db_export.py")
        logger.info("   This updates JSON for website and Excel for review")

    except Exception as e:
        logger.exception(f"Import failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
