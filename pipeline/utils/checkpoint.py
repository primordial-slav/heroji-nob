"""
Checkpoint manager for resumable processing.

Saves state after each batch to allow resuming interrupted runs.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional


class CheckpointManager:
    """
    Manages checkpointing for resumable batch processing.

    Saves state to a JSON file after each batch, allowing
    interrupted runs to resume from the last completed batch.

    Usage:
        cp = CheckpointManager(workspace / "03_checkpoint.json")

        if args.resume and cp.exists():
            state = cp.load()
            start_batch = state['last_completed_batch'] + 1
            results = state['results']
        else:
            start_batch = 0
            results = []

        for batch_num in range(start_batch, total_batches):
            # process batch...
            results.extend(batch_results)
            cp.save(batch_num, results, total_tokens, confidence_counts)

        cp.clear()  # Remove checkpoint on success
    """

    def __init__(self, checkpoint_path: Path, logger: logging.Logger = None):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_path: Path to checkpoint JSON file
            logger: Logger instance
        """
        self.path = Path(checkpoint_path)
        self.logger = logger or logging.getLogger(__name__)

    def exists(self) -> bool:
        """Check if a checkpoint file exists."""
        return self.path.exists()

    def load(self) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint state from file.

        Returns:
            Dict with checkpoint state or None if not found

        State contains:
            - last_completed_batch: int
            - results: List[dict]
            - total_tokens: int
            - confidence_counts: Dict[str, int]
            - saved_at: str (ISO timestamp)
            - source_file: str
        """
        if not self.exists():
            return None

        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            self.logger.info(
                f"Loaded checkpoint: batch {state.get('last_completed_batch', -1)}, "
                f"{len(state.get('results', []))} results"
            )
            return state
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return None

    def save(
        self,
        last_completed_batch: int,
        results: List[Dict[str, Any]],
        total_tokens: int,
        confidence_counts: Dict[str, int],
        source_file: str = None,
        extra_data: Dict[str, Any] = None
    ) -> None:
        """
        Save checkpoint state to file.

        Args:
            last_completed_batch: Index of last completed batch (0-based)
            results: List of extracted soldier records
            total_tokens: Total tokens used so far
            confidence_counts: Dict of confidence level counts
            source_file: Name of source file being processed
            extra_data: Any additional data to save
        """
        state = {
            'last_completed_batch': last_completed_batch,
            'results': results,
            'total_tokens': total_tokens,
            'confidence_counts': confidence_counts,
            'saved_at': datetime.now().isoformat(),
            'source_file': source_file,
        }

        if extra_data:
            state.update(extra_data)

        try:
            # Write to temp file first, then rename for atomicity
            temp_path = self.path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

            # Atomic rename
            temp_path.replace(self.path)

            self.logger.debug(
                f"Checkpoint saved: batch {last_completed_batch}, "
                f"{len(results)} results"
            )
        except IOError as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            raise

    def clear(self) -> None:
        """Remove checkpoint file (call on successful completion)."""
        if self.path.exists():
            try:
                self.path.unlink()
                self.logger.info("Checkpoint cleared (processing complete)")
            except IOError as e:
                self.logger.warning(f"Failed to clear checkpoint: {e}")

    def get_resume_info(self) -> Optional[str]:
        """Get human-readable resume info if checkpoint exists."""
        state = self.load()
        if not state:
            return None

        return (
            f"Found checkpoint from {state.get('saved_at', 'unknown')}:\n"
            f"  - Last batch: {state.get('last_completed_batch', -1)}\n"
            f"  - Results so far: {len(state.get('results', []))}\n"
            f"  - Tokens used: {state.get('total_tokens', 0):,}\n"
            f"  - Source: {state.get('source_file', 'unknown')}"
        )
