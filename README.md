# Discord Mirror Bot

Mirrors messages from one Discord channel to another through a webhook. The application separates configuration, HTTP access, message transformation, persistence, and runtime orchestration into independent components.

## Mirrored content

- Message text and up to 10 embeds per message.
- Embed titles, descriptions, colors, links, authors, footers, fields, images, and thumbnails.
- Text and embeds contained in the same message, without discarding either.
- Links to attachments and stickers.
- The author's server nickname, global name, username, and avatar.
- Stable aliases (`user1`, `user2`, and so on) when incognito mode is enabled.

Mentions are disabled at the destination to avoid notifying users, roles, or `@everyone` again.

## Requirements

- Python 3.9 or newer.
- A Discord bot with access to the source channel and the **Read Message History** permission.
- A webhook in the destination channel.

Do not use a personal account token. Self-bots violate Discord's terms. Use a bot created through the official developer portal.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`:

```dotenv
DISCORD_TOKEN=your_bot_token
SOURCE_CHANNEL_ID=123456789012345678
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

POLL_INTERVAL_SECONDS=5
INCOGNITO_MODE=false
FETCH_LIMIT=50
```

The `.env` file is ignored by Git. Never commit tokens or webhook URLs.

Start the service with either command:

```powershell
python main.py
python -m mirror_bot
```

On its first run, the application processes the latest `FETCH_LIMIT` messages. It then stores the last delivered message ID for each job in `data/state.json`. A cursor advances only after the webhook confirms delivery, so a temporary failure does not lose messages.

## Multiple mirrors

Copy `jobs.example.json` to `jobs.json`. This file contains only options and the names of environment variables holding secrets; the secret values remain in `.env`.

```dotenv
MIRROR_JOBS_FILE=jobs.json
DISCORD_TOKEN=shared_token
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
ALERTS_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

Each job maintains an independent cursor, even when multiple jobs read the same source channel.

## Project structure

```text
main.py                         Backwards-compatible entry point
mirror_bot/domain/              Immutable models with no HTTP or file access
mirror_bot/application/         Use case, ports, and payload construction
mirror_bot/adapters/discord/    Discord input and webhook output
mirror_bot/adapters/persistence Atomic, thread-safe JSON state
mirror_bot/adapters/http.py     Shared retries and rate-limit handling
mirror_bot/runtime.py           Polling, worker threads, and graceful shutdown
mirror_bot/config.py            .env and jobs.json loading and validation
mirror_bot/properties.py        Discord endpoints and HTTP client properties
mirror_bot/app.py               Composition root
tests/                          Unit tests
```

## Design

```text
Discord JSON -> DiscordSourceAdapter -> Message
                                        |
                                  MirrorService
                                        |
Discord API  <- DiscordWebhookAdapter <- WebhookPayload

                 MirrorState port
                        ^
                        |
                JsonStateAdapter
```

- API dictionaries exist only inside the Discord adapter. `DiscordMessageMapper` immediately converts them into immutable dataclasses.
- `application/ports.py` defines `MessageSource`, `MessageDestination`, and `MirrorState`. The use case does not depend on Requests, Discord, or JSON.
- `MirrorService` processes one batch; `PollingRunner` decides when to repeat it. Keeping these responsibilities separate makes the logic testable without sleeps or threads.
- `WebhookPayloadBuilder` is a pure model-to-model transformation that applies Discord's limits without accessing files or making requests.
- The Discord source and webhook adapters have separate contracts and errors. `adapters/http.py` shares only transport and retry behavior.
- `JsonStateAdapter` is the only component that writes state. It uses an atomic replacement guarded across threads.
- `app.py` is the composition root and the only place that selects which implementations are connected to each port.
- Secrets are excluded from configuration representations and are never stored in job files.
- `properties.py` centralizes structural URLs and exposes them through explicitly named functions. Concrete webhook URLs and tokens remain in `.env` because they are deployment secrets.

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m coverage run -m unittest discover
python -m coverage report
```

Coverage includes branches and must remain above 90%. GitHub Actions runs the same suite on Python 3.9, 3.11, and 3.13.

## Responsible use

Respect Discord's terms, server permissions, and member privacy. This project does not bypass access controls: the bot can read only channels for which it has explicit permission.
