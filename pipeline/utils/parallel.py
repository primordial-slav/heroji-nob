"""
Parallel processing for soldier extraction.

Uses ThreadPoolExecutor for concurrent API calls with rate limiting.
"""

import time
import logging
import threading
from typing import List, Dict, Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class ParallelExtractor:
    """
    Parallel batch processor for soldier extraction.

    Uses ThreadPoolExecutor for concurrent API calls with:
        - Configurable number of workers (max 5)
        - Rate limiting delay between submissions
        - Thread-safe results collection
        - Error tracking per batch

    Usage:
        extractor = ParallelExtractor(
            extract_fn=extract_batch,
            workers=3,
            rate_limit_delay=0.5
        )

        results = extractor.process_batches(batches)
    """

    MAX_WORKERS = 5

    def __init__(
        self,
        extract_fn: Callable[[List[str], int], Dict],
        workers: int = 1,
        rate_limit_delay: float = 0.2,
        logger: logging.Logger = None
    ):
        """
        Initialize parallel extractor.

        Args:
            extract_fn: Function to call for each batch
                        Signature: (lines: List[str], batch_index: int) -> Dict
            workers: Number of parallel workers (1-5)
            rate_limit_delay: Delay between batch submissions (seconds)
            logger: Logger instance
        """
        self.extract_fn = extract_fn
        self.workers = min(max(1, workers), self.MAX_WORKERS)
        self.rate_limit_delay = rate_limit_delay
        self.logger = logger or logging.getLogger(__name__)

        # Thread-safe result collection
        self._lock = threading.Lock()
        self._results: Dict[int, Dict] = {}
        self._errors: Dict[int, Exception] = {}
        self._tokens_used = 0

    def process_batches(
        self,
        batches: List[List[str]],
        start_batch: int = 0,
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Process multiple batches in parallel.

        Args:
            batches: List of line batches to process
            start_batch: Starting batch index (for resume)
            progress_callback: Optional callback(completed, total, tokens)

        Returns:
            Dict with:
                - results: Dict[batch_index, result_dict]
                - errors: Dict[batch_index, exception]
                - total_tokens: int
        """
        total_batches = len(batches)
        self._results.clear()
        self._errors.clear()
        self._tokens_used = 0

        if self.workers == 1:
            # Single-threaded mode - simpler, no overhead
            return self._process_sequential(
                batches, start_batch, progress_callback
            )

        self.logger.info(
            f"Processing {total_batches - start_batch} batches "
            f"with {self.workers} workers"
        )

        completed = 0

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all batches with rate limiting
            futures = {}
            for batch_idx in range(start_batch, total_batches):
                future = executor.submit(
                    self._process_single_batch,
                    batches[batch_idx],
                    batch_idx
                )
                futures[future] = batch_idx

                # Rate limiting between submissions
                if batch_idx < total_batches - 1:
                    time.sleep(self.rate_limit_delay)

            # Collect results as they complete
            for future in as_completed(futures):
                batch_idx = futures[future]
                completed += 1

                try:
                    future.result()  # Raise any exception
                except Exception as e:
                    self.logger.error(
                        f"Batch {batch_idx} failed: {type(e).__name__}: {e}"
                    )

                if progress_callback:
                    progress_callback(
                        completed,
                        total_batches - start_batch,
                        self._tokens_used
                    )

        return {
            'results': dict(self._results),
            'errors': dict(self._errors),
            'total_tokens': self._tokens_used,
        }

    def _process_sequential(
        self,
        batches: List[List[str]],
        start_batch: int,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Process batches sequentially (single-threaded)."""
        total_batches = len(batches)

        for batch_idx in range(start_batch, total_batches):
            self._process_single_batch(batches[batch_idx], batch_idx)

            if progress_callback:
                progress_callback(
                    batch_idx - start_batch + 1,
                    total_batches - start_batch,
                    self._tokens_used
                )

        return {
            'results': dict(self._results),
            'errors': dict(self._errors),
            'total_tokens': self._tokens_used,
        }

    def _process_single_batch(
        self,
        batch_lines: List[str],
        batch_index: int
    ) -> None:
        """
        Process a single batch and store results thread-safely.

        Args:
            batch_lines: Lines to process
            batch_index: Index of this batch
        """
        try:
            result = self.extract_fn(batch_lines, batch_index)

            with self._lock:
                self._results[batch_index] = result
                self._tokens_used += result.get('tokens', 0)

            self.logger.debug(
                f"Batch {batch_index}: {len(result.get('soldiers', []))} soldiers, "
                f"{result.get('tokens', 0)} tokens"
            )

        except Exception as e:
            with self._lock:
                self._errors[batch_index] = e

            self.logger.error(
                f"Batch {batch_index} error: {type(e).__name__}: {e}"
            )
            raise

    def get_ordered_results(self) -> List[Dict]:
        """Get all soldier results in batch order."""
        soldiers = []
        for batch_idx in sorted(self._results.keys()):
            batch_result = self._results[batch_idx]
            soldiers.extend(batch_result.get('soldiers', []))
        return soldiers
