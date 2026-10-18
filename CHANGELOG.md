# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-10-19

### Fixed

- README image and links now use absolute URLs so the banner renders correctly on PyPI
  (relative `assets/…` paths only worked on GitHub).
- `publish.yml` now declares the `id-token: write` permission required by Trusted Publishing.

### Added

- Repository banner (`assets/banner.svg`) and logo (`assets/logo.svg`) using the official
  Bale brand gradient, shown at the top of both READMEs.

## [0.1.0] - 2026-10-18

### Added

- `AsyncBaleClient`: full asynchronous client (HTTP + JSON + multipart uploads) covering every
  method documented in the Bale Bot API (`getMe`, sending messages/media, chat administration,
  message editing, stickers, payments, webhooks, `getUpdates`, …).
- `BaleClient`: fully typed synchronous client sharing the same implementation.
- Typed result objects for every API type (`User`, `Chat`, `ChatFullInfo`, `Message`,
  `CallbackQuery`, `ChatMember` hierarchy, `Sticker`, `SuccessfulPayment`, `Transaction`, …).
- Input builders: `InlineKeyboardMarkup`, `ReplyKeyboardMarkup`, `InputMedia*`, `InputFile`,
  `InputSticker`, `LabeledPrice`.
- Bale-specific methods that do not exist in Telegram libraries: `ask_review`, `inquire_transaction`.
- Business (bulk messaging) API support via `business=True`
  (`https://tapi.bale.ai/business/bot<token>/…`).
- Transparent rate-limit handling (`TooManyRequests` with `retry_after`) and optional automatic
  retries for `429`/`5xx` responses.
- Long-polling helpers: `run_polling` (async) and `run_polling_sync`.
- Webhook helpers: `parse_update`.
- Mini App server-side helpers: `validate_init_data`, `WebAppInitData`, `WebAppUser`.
- Markdown formatting helpers matching Bale rules (`bold`, `italic`, `link`, `inline_note`).
- GitHub Actions workflow `publish.yml` publishing releases to PyPI via Trusted Publishing (OIDC).

[Unreleased]: https://github.com/mrhamidrezam/baleRobot/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/mrhamidrezam/baleRobot/releases/tag/v0.1.1
[0.1.0]: https://github.com/mrhamidrezam/baleRobot/releases/tag/v0.1.0
