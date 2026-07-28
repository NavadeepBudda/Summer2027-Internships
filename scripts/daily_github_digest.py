#!/usr/bin/env python3
"""Create a GitHub-ready digest of newly posted Summer 2027 internships."""

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

TIME_ZONE = ZoneInfo("America/New_York")
TARGET_TERM = "Summer 2027"
REPOSITORY_URL = "https://github.com/NavadeepBudda/Summer2027-Internships"
UPSTREAM_URL = "https://github.com/SimplifyJobs/Summer2026-Internships"
DEFAULT_LISTINGS_PATH = Path(".github/scripts/listings.json")

type Listing = dict[str, Any]


def should_deliver(event_name: str, schedule_expression: str, now: datetime) -> bool:
    """Decide whether this is the correct Eastern-time schedule.

    GitHub may start scheduled workflows substantially late, so this uses the
    triggering cron expression and the day's UTC offset instead of the actual
    start hour.
    """
    if event_name == "workflow_dispatch":
        return True

    utc_offset = now.utcoffset()
    return (schedule_expression == "11 20 * * *" and utc_offset == timedelta(hours=-4)) or (
        schedule_expression == "11 21 * * *" and utc_offset == timedelta(hours=-5)
    )


def load_listings(path: Path) -> list[Listing]:
    """Load the listing database."""
    with path.open() as handle:
        listings: list[Listing] = json.load(handle)
    return listings


def listings_posted_on(listings: list[Listing], target_date: date) -> list[Listing]:
    """Return active, visible Summer 2027 listings posted on the target date."""
    matches = []
    for listing in listings:
        posted_at = datetime.fromtimestamp(listing["date_posted"], TIME_ZONE)
        if (
            listing.get("active", False)
            and listing.get("is_visible", False)
            and TARGET_TERM in listing.get("terms", [])
            and posted_at.date() == target_date
        ):
            matches.append(listing)

    return sorted(matches, key=lambda item: (item["company_name"].lower(), item["title"].lower()))


def escape_markdown(value: object) -> str:
    """Escape characters that would break a Markdown table cell."""
    return str(value).replace("|", r"\|").replace("\n", " ")


def format_markdown(listings: list[Listing], target_date: date) -> str:
    """Build the GitHub issue body."""
    count = len(listings)
    position_label = "positions" if count != 1 else "position"
    lines = [
        f"# {count} new {TARGET_TERM} {position_label}",
        "",
        f"Active Summer 2027 positions posted on **{target_date:%B %d, %Y}**:",
        "",
    ]

    if listings:
        lines.extend(
            [
                "| Company | Role | Location | Category | Application |",
                "| --- | --- | --- | --- | :---: |",
            ]
        )
        for listing in listings:
            company = escape_markdown(listing["company_name"])
            title = escape_markdown(listing["title"])
            locations = escape_markdown(", ".join(listing.get("locations", [])) or "Location not listed")
            category = escape_markdown(listing.get("category", "Other"))
            url = str(listing["url"])
            lines.append(f"| {company} | {title} | {locations} | {category} | [Apply]({url}) |")
    else:
        lines.append("No new active Summer 2027 positions were posted today.")

    lines.extend(
        [
            "",
            f"[Browse the complete Summer 2027 list]({REPOSITORY_URL})",
            "",
            "---",
            "",
            f"Listing data and monitoring are credited to [Simplify](https://simplify.jobs/) and "
            f"[Pitt CSC](https://pittcsc.org/). [View the upstream project]({UPSTREAM_URL}).",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="Digest date in YYYY-MM-DD format; defaults to today in New York")
    parser.add_argument("--listings", type=Path, default=DEFAULT_LISTINGS_PATH)
    parser.add_argument("--output", type=Path, help="Write Markdown to this path instead of standard output")
    return parser.parse_args()


def main() -> None:
    """Build the daily digest."""
    args = parse_args()
    target_date = date.fromisoformat(args.date) if args.date else datetime.now(TIME_ZONE).date()
    listings = listings_posted_on(load_listings(args.listings), target_date)
    digest = format_markdown(listings, target_date)

    if args.output:
        args.output.write_text(digest)
    else:
        print(digest)


if __name__ == "__main__":
    main()
