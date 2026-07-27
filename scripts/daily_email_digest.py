#!/usr/bin/env python3
"""Email a daily digest of newly posted Summer 2027 internships."""

import argparse
import html
import json
import os
import smtplib
from datetime import date, datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

TIME_ZONE = ZoneInfo("America/New_York")
TARGET_TERM = "Summer 2027"
REPOSITORY_URL = "https://github.com/NavadeepBudda/Summer2027-Internships"
DEFAULT_LISTINGS_PATH = Path(".github/scripts/listings.json")

type Listing = dict[str, Any]


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


def format_plain_text(listings: list[Listing], target_date: date) -> str:
    """Build the plain-text email body."""
    position_label = "positions" if len(listings) != 1 else "position"
    heading = f"{len(listings)} new {TARGET_TERM} {position_label} on {target_date:%B %d, %Y}"
    lines = [heading, ""]

    if not listings:
        lines.extend(["No new active Summer 2027 positions were posted today.", ""])
    else:
        for listing in listings:
            locations = ", ".join(listing.get("locations", [])) or "Location not listed"
            lines.extend(
                [
                    f"{listing['company_name']} — {listing['title']}",
                    f"Location: {locations}",
                    f"Category: {listing.get('category', 'Other')}",
                    f"Apply: {listing['url']}",
                    "",
                ]
            )

    lines.extend(
        [
            f"Browse the complete Summer 2027 list: {REPOSITORY_URL}",
            "",
            "Listing data and monitoring are credited to Simplify and Pitt CSC.",
            "Upstream project: https://github.com/SimplifyJobs/Summer2026-Internships",
        ]
    )
    return "\n".join(lines)


def format_html(listings: list[Listing], target_date: date) -> str:
    """Build the HTML email body."""
    count = len(listings)
    rows = []
    for listing in listings:
        company = html.escape(str(listing["company_name"]))
        title = html.escape(str(listing["title"]))
        locations = html.escape(", ".join(listing.get("locations", [])) or "Location not listed")
        category = html.escape(str(listing.get("category", "Other")))
        url = html.escape(str(listing["url"]), quote=True)
        rows.append(
            "<tr>"
            f"<td style='padding:8px;border:1px solid #ddd'><strong>{company}</strong></td>"
            f"<td style='padding:8px;border:1px solid #ddd'>{title}</td>"
            f"<td style='padding:8px;border:1px solid #ddd'>{locations}</td>"
            f"<td style='padding:8px;border:1px solid #ddd'>{category}</td>"
            f"<td style='padding:8px;border:1px solid #ddd'><a href='{url}'>Apply</a></td>"
            "</tr>"
        )

    if rows:
        content = (
            "<table style='border-collapse:collapse;width:100%'>"
            "<thead><tr>"
            "<th style='padding:8px;border:1px solid #ddd;text-align:left'>Company</th>"
            "<th style='padding:8px;border:1px solid #ddd;text-align:left'>Role</th>"
            "<th style='padding:8px;border:1px solid #ddd;text-align:left'>Location</th>"
            "<th style='padding:8px;border:1px solid #ddd;text-align:left'>Category</th>"
            "<th style='padding:8px;border:1px solid #ddd;text-align:left'>Application</th>"
            "</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
    else:
        content = "<p>No new active Summer 2027 positions were posted today.</p>"

    return (
        "<html><body style='font-family:Arial,sans-serif;color:#222'>"
        f"<h2>{count} new {TARGET_TERM} position{'s' if count != 1 else ''} on {target_date:%B %d, %Y}</h2>"
        f"{content}"
        f"<p><a href='{REPOSITORY_URL}'>Browse the complete Summer 2027 list</a></p>"
        "<hr>"
        "<p style='font-size:12px;color:#666'>Listing data and monitoring are credited to "
        "<a href='https://simplify.jobs/'>Simplify</a> and "
        "<a href='https://pittcsc.org/'>Pitt CSC</a>. "
        "<a href='https://github.com/SimplifyJobs/Summer2026-Internships'>View the upstream project</a>.</p>"
        "</body></html>"
    )


def send_digest(listings: list[Listing], target_date: date) -> None:
    """Send the digest using Gmail SMTP credentials stored in environment variables."""
    username = os.environ.get("DIGEST_EMAIL_USERNAME")
    app_password = os.environ.get("DIGEST_EMAIL_APP_PASSWORD")
    recipient = os.environ.get("DIGEST_EMAIL_TO")
    missing = [
        name
        for name, value in [
            ("DIGEST_EMAIL_USERNAME", username),
            ("DIGEST_EMAIL_APP_PASSWORD", app_password),
            ("DIGEST_EMAIL_TO", recipient),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required email configuration: {', '.join(missing)}")
    assert username is not None
    assert app_password is not None
    assert recipient is not None

    message = EmailMessage()
    message["From"] = username
    message["To"] = recipient
    message["Subject"] = f"{len(listings)} new Summer 2027 internships — {target_date:%b %d}"
    message.set_content(format_plain_text(listings, target_date))
    message.add_alternative(format_html(listings, target_date), subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(username, app_password.replace(" ", ""))
        smtp.send_message(message)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="Digest date in YYYY-MM-DD format; defaults to today in New York")
    parser.add_argument("--listings", type=Path, default=DEFAULT_LISTINGS_PATH)
    parser.add_argument("--dry-run", action="store_true", help="Print the digest without sending email")
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="Send only when the current New York hour is 4 PM; handles daylight saving time",
    )
    return parser.parse_args()


def main() -> None:
    """Build and optionally send the daily digest."""
    args = parse_args()
    now = datetime.now(TIME_ZONE)

    if args.scheduled and now.hour != 16:
        print(f"Skipping duplicate UTC schedule at {now:%H:%M %Z}; it is not the 4 PM Eastern hour.")
        return

    target_date = date.fromisoformat(args.date) if args.date else now.date()
    listings = listings_posted_on(load_listings(args.listings), target_date)

    if args.dry_run:
        print(format_plain_text(listings, target_date))
        return

    send_digest(listings, target_date)
    print(f"Sent digest with {len(listings)} Summer 2027 positions for {target_date.isoformat()}.")


if __name__ == "__main__":
    main()
