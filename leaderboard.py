"""
leaderboard.py — Persistent top-scores storage using a JSON file.

The leaderboard stores the top N survival times, sorted descending
(longest survival = best).  It persists between application restarts
via a simple JSON file.  All read/write operations are wrapped in
try/except so a corrupted file never crashes the application.
"""

import json
import os

import config as cfg


class Leaderboard:
    """
    Manages a persistent top-scores list.

    Usage:
        lb = Leaderboard()
        rank = lb.submit(45.3)          # Returns rank (0-indexed) or -1
        top = lb.get_scores()           # Returns sorted list of floats
        lb.reset()                      # Clear all scores
    """

    def __init__(self, filepath=None):
        self.filepath = filepath or cfg.LEADERBOARD_FILE
        self.max_entries = cfg.LEADERBOARD_MAX_ENTRIES
        self.scores = self._load()

    def _load(self):
        """
        Load scores from the JSON file.  If the file doesn't exist or
        is corrupted, return an empty list rather than crashing.
        """
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
            # Validate: must be a list of numbers
            if isinstance(data, list):
                return sorted([float(s) for s in data if isinstance(s, (int, float))],
                              reverse=True)[:self.max_entries]
        except (json.JSONDecodeError, ValueError, TypeError, IOError):
            pass
        return []

    def _save(self):
        """Write scores to disk.  Silently fails on I/O error."""
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.scores, f, indent=2)
        except IOError:
            pass  # Non-fatal: we just lose persistence

    def submit(self, survival_time):
        """
        Submit a new score.  Returns a tuple (rank, is_new_highscore)
        where rank is the 0-indexed position in the leaderboard (-1 if
        the score didn't make the board), and is_new_highscore is True
        if this is the new #1 score.

        The score is inserted into the sorted list and the file is
        saved immediately.
        """
        survival_time = round(survival_time, 1)

        # Check if this beats the current #1
        is_highscore = len(self.scores) == 0 or survival_time > self.scores[0]

        # Insert in sorted position
        rank = -1
        inserted = False
        for i, existing in enumerate(self.scores):
            if survival_time >= existing:
                self.scores.insert(i, survival_time)
                rank = i
                inserted = True
                break

        if not inserted:
            if len(self.scores) < self.max_entries:
                self.scores.append(survival_time)
                rank = len(self.scores) - 1
            else:
                # Didn't make the board
                return -1, False

        # Trim to max entries
        self.scores = self.scores[:self.max_entries]

        self._save()
        return rank, is_highscore

    def get_scores(self):
        """Return a copy of the current scores list (descending order)."""
        return list(self.scores)

    def reset(self):
        """Clear all scores and save the empty file."""
        self.scores = []
        self._save()
