# Daily Email Digest Setup

The `Email Daily Summer 2027 Digest` GitHub Actions workflow sends a regular email at approximately
4:11 PM Eastern Time with every active Summer 2027 position posted that day. It sends a short
“no new positions” email when there were no additions.

GitHub schedules use UTC, so the workflow runs at both possible Eastern UTC offsets and sends only
during the 4 PM `America/New_York` hour. This keeps the delivery time correct across daylight saving
time. GitHub Actions schedules can occasionally start a few minutes late.

## Configure Gmail

1. Turn on 2-Step Verification for the Google Account that will send the digest.
2. Create a dedicated Google App Password named `Summer 2027 GitHub Digest`.
3. Open this repository’s **Settings → Secrets and variables → Actions** page.
4. Create these repository secrets:

| Secret | Value |
| --- | --- |
| `DIGEST_EMAIL_USERNAME` | The complete Gmail address that sends the digest |
| `DIGEST_EMAIL_APP_PASSWORD` | The dedicated 16-character Google App Password |
| `DIGEST_EMAIL_TO` | The email address that should receive the digest |

Never use your normal Google Account password and never commit an App Password to the repository.

After adding all three secrets, open **Actions → Email Daily Summer 2027 Digest → Run workflow** to
send a test digest immediately.

Google’s official App Password instructions:
https://support.google.com/accounts/answer/185833

GitHub’s official repository-secret instructions:
https://docs.github.com/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
