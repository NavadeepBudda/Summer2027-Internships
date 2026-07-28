"""Tests for the daily Summer 2027 GitHub digest."""

import sys
import unittest
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.daily_github_digest import TIME_ZONE, format_markdown, listings_posted_on, should_deliver


def make_listing(**overrides: object) -> dict[str, object]:
    """Create a representative listing for tests."""
    listing: dict[str, object] = {
        "company_name": "Example",
        "title": "Software Engineer Intern",
        "locations": ["New York, NY"],
        "category": "Software",
        "url": "https://example.com/apply",
        "date_posted": int(datetime(2026, 7, 27, 9, 30, tzinfo=TIME_ZONE).timestamp()),
        "terms": ["Summer 2027"],
        "active": True,
        "is_visible": True,
    }
    listing.update(overrides)
    return listing


class DailyGitHubDigestTests(unittest.TestCase):
    """Verify filtering and digest formatting."""

    def test_filters_to_active_visible_target_term_and_date(self) -> None:
        target_date = date(2026, 7, 27)
        listings = [
            make_listing(),
            make_listing(company_name="Closed", active=False),
            make_listing(company_name="Hidden", is_visible=False),
            make_listing(company_name="Wrong term", terms=["Summer 2026"]),
            make_listing(
                company_name="Wrong date",
                date_posted=int(datetime(2026, 7, 26, 23, 59, tzinfo=TIME_ZONE).timestamp()),
            ),
        ]

        matches = listings_posted_on(listings, target_date)  # type: ignore[arg-type]

        self.assertEqual([listing["company_name"] for listing in matches], ["Example"])

    def test_markdown_includes_role_and_credits(self) -> None:
        body = format_markdown([make_listing()], date(2026, 7, 27))  # type: ignore[list-item]

        self.assertIn("| Example | Software Engineer Intern |", body)
        self.assertIn("[Apply](https://example.com/apply)", body)
        self.assertIn("credited to [Simplify]", body)

    def test_markdown_handles_no_new_roles(self) -> None:
        body = format_markdown([], date(2026, 7, 27))

        self.assertIn("# 0 new Summer 2027 positions", body)
        self.assertIn("No new active", body)

    def test_delayed_summer_schedule_still_delivers(self) -> None:
        delayed_start = datetime(2026, 7, 27, 17, 20, tzinfo=TIME_ZONE)

        self.assertTrue(should_deliver("schedule", "11 20 * * *", delayed_start))
        self.assertFalse(should_deliver("schedule", "11 21 * * *", delayed_start))

    def test_delayed_winter_schedule_still_delivers(self) -> None:
        delayed_start = datetime(2027, 1, 27, 18, 20, tzinfo=TIME_ZONE)

        self.assertTrue(should_deliver("schedule", "11 21 * * *", delayed_start))
        self.assertFalse(should_deliver("schedule", "11 20 * * *", delayed_start))

    def test_manual_dispatch_always_delivers(self) -> None:
        now = datetime(2026, 7, 27, 9, 0, tzinfo=TIME_ZONE)

        self.assertTrue(should_deliver("workflow_dispatch", "", now))


if __name__ == "__main__":
    unittest.main()
