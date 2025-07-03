# Gemini Agent Context: yt_subs_dl

## Project Overview

This project, `yt_subs_dl`, is a Python-based command-line tool for downloading and formatting subtitles from YouTube videos. It extracts subtitle text, merges segments, and intelligently adds newlines based on pause durations. It also handles language-specific text formatting.

## Tech Stack

- **Language:** Python
- **Environment Management:** Nix Flakes
- **Core Libraries:**
  - `yt-dlp`: For downloading video metadata and subtitles.
  - `requests`: (Included in the environment, available for use).

## gemini-cli Chat Rule

- The AI of `gemini-cli` must respond in the same language as the user's prompt.
  - Therefore, please think according to the following steps:
    1. First, internally translate the user's prompt into English.
    2. When Answering:
      1. Internally prepare the response in English.
      2. Finally, translate the response into the user's prompt language and display it.

## Development Environment

The development environment is fully managed by Nix to ensure reproducibility.

1.  **Setup:** Run `nix develop` in the project root. This command will install all necessary dependencies, including Python and the required packages, into a temporary shell.
2.  **Execution:** All development commands, including running the script, should be executed within this shell.

## Key Files

- **`yt_subs_dl.py`**: The main entry point and application logic.
- **`flake.nix`**: Defines the Nix Flake, including all Python dependencies. To add or update packages, modify the `buildInputs` list in this file.
- **`README.md`**: User-facing documentation with usage instructions.

## Development Workflow

- **Running the script:**
  ```bash
  nix run .#default "<YOUTUBE_VIDEO_URL>"
  ```
- **Adding Dependencies:** Edit the `buildInputs` list in `flake.nix` and re-run `nix develop` to update the environment.
  - Also add dependecies to `requirements.txt` for compatibility with `pip`.

### Development AI Rule

- Testing
  - Add test in `./tests` diretctories if you make new function.
  - Never change the things already exists in `./tests`.
    - Only unless the function specification change is directly requested in the prompt.
- Language
  - Write comments and documentations in **English**.
- Document
  - If you make changes that affect users, update `README.md`.
  - If you define new types or functions, write documentation.
- Git
  - Never try to run the `git` command unless the user directly requests the execution of a git command in the prompt.

### Testing and Linting

The development environment includes `pytest` for testing and `ruff` for linting and formatting.

- **Testing (pytest):**
  ```bash
  nix run .#test
  ```
- **Linting & Formatting (Ruff):**
  ```bash
  # To check for issues:
  nix run .#format -- check .
  # To format code:
  nix run .#format -- format .
- **Check compatibility with pip:**
  ```bash
  nix run .#run-from-requirements-install
  ```

### Runtime Arguments Rules

- If you need a URL argument to test the functionality, use "https://www.youtube.com/watch?v=CGMTguMGPt0"

## Commit Rule

- This project uses gitflow.
- This project uses gitmoji.
- Commit message must be in English.
- Commit title format: `<type>: <emoji>(<context>) <body>`
  (e.g., 'refactor: :recycle:(backend) split `calc_fraction()` into multiple functions')
  - Select one of emoji from the list below apppropriate to show context of the commit.
    - Refer `kind` of emoji.
  - `<type>`: Commit type (e.g., fix, feat, docs). `type` column in the table.
    - Must match one of the IDs from the emoji list.
  - `<emoji>`: The emoji, `emoji` column in the table,
    written as a string enclosed in double colons
    (e.g., `:bug:`, `:sparkles:`, `:books:`, `:rocket:`), NOT as a Unicode emoji.
    - When writing the emoji. always use the double colon notation (e.g., `:sparkles:`),
      not the Unicode emoji symbol. 
      - For instance, write `:sparkles:` instead of ✨. 
  - `<context>`: The context of the commit, representing an externally visible unit,
    such as a module or issue number (e.g., `main`, `reader`, `fix: #1234`, `docs: #1234`).
    - `(<context>)` is optional, including the parentheses.
    - Avoid using code-specific units like function names or class names as context.
    - If the change type is broad or affects multiple areas, omit the context.
  - `<body>`: The description of commit. 
    (e.g. `add function to calculate the length of meridian line`)
- Optionally, include a commit body for:
  - Details on what was changed.
  - Explanation of why the change was made.
- If you make commit body, please separate it from the title with line break.

### Conditions of the sentence of commit message

- Use universally understandable abbreviations.
- Keep titles under 80 characters, ideally under 50 unless necessary.
- Limit the body to 300 characters (5 lines).
  - Each line is under 80 characters.
  - Each paragraph is separated by a blank line.
  - Without counting the blank lines.

### gitmojis

The meaning of row:
- `type`, `emoji`: as above
- `description`: The description of emoji.
- `kind`: The category of emoji.
- `utf8`: emoji in utf8 format.

| type           | emoji                       | description                                                          | kind        | utf8 |
| :------------- | :-------------------------- | :------------------------------------------------------------------- | :---------- | :--- |
| feat           | :sparkles:                  | introduce new features                                               | general     | ✨   |
| breaking       | :boom:                      | breaking: Introduce breaking changes                                 | general     | 💥   |
| validation     | :safety_vest:               | validation: Add or update code related to validation.                | general     | 🦺   |
| perf           | :zap:                       | performance: improve performance                                     | performance | ⚡️  |
| thread         | :thread:                    | thread: Add or update code related to multithreading or concurrency. | performance | 🧵   |
| comment        | :bulb:                      | comment: Add or update comments in source code.                      | codes       | 💡   |
| refactor       | :recycle:                   | recycle: refactor code                                               | codes       | ♻️   |
| fmt            | :art:                       | format: improve structure / format of the code                       | codes       | 🎨   |
| rm             | :fire:                      | remove: remove code or files                                         | codes       | 🔥   |
| archit         | :building_construction:     | architecture: Make architectural changes.                            | codes       | 🏗️   |
| types          | :label:                     | types: Add or update types.                                          | codes       | 🏷️   |
| deprecate      | :wastebasket:               | deprecate: Deprecate code that needs to be cleaned up.               | codes       | 🗑️   |
| UI             | :lipstick:                  | UI: add or update the UI and style files                             | looks       | 💄   |
| txt            | :speech_balloon:            | text: Add or update text and literals.                               | looks       | 💬   |
| locale         | :globe_with_meridians:      | locale: Internationalization and localization.                       | looks       | 🌐   |
| a11y           | :wheelchair:                | a11y: Improve accessibility.                                         | looks       | ♿️  |
| UX             | :children_crossing:         | UX: Improve user experience / usability.                             | looks       | 🚸   |
| hot-fix        | :ambulance:                 | hot-fix: critical hotfix                                             | fix         | 🚑️  |
| small-fix      | :adhesive_bandage:          | small-fix: simple fix for a non-critical issue                       | fix         | 🩹   |
| bug            | :bug:                       | bug: fix a bug                                                       | fix         | 🐛   |
| typo           | :pencil2:                   | typo: Fix typos.                                                     | fix         | ✏️   |
| warning-fix    | :rotating_light:            | warning-fix: fix compiler / linter warnings                          | fix         | 🚨   |
| revert         | :rewind:                    | revert: revert changes                                               | fix         | ⏪️  |
| secure         | :lock:                      | secure: Fix security issues                                          | fix         | 🔒️  |
| DB             | :card_file_box:             | database: Perform database related changes.                          | resources   | 🗃️   |
| rename         | :truck:                     | rename: Move or rename resources (e.g.: files, paths, routes).       | resources   | 🚚   |
| secret         | :closed_lock_with_key:      | secret: add or update secrets                                        | resources   | 🔐   |
| assets         | :bento:                     | assets: Add or update assets.                                        | resources   | 🍱   |
| seed           | :seedling:                  | seed: Add or update seed files.                                      | resources   | 🌱   |
| doc            | :memo:                      | doc: add or update documentation                                     | document    | 📝   |
| license        | :page_facing_up:            | license: Add or update license.                                      | document    | 📄   |
| log            | :loud_sound:                | add log: Add or update logs.                                         | document    | 🔊   |
| rm-log         | :mute:                      | remove log: Remove logs.                                             | document    | 🔇   |
| test           | :white_check_mark:          | test: add, update, or pass tests                                     | test        | ✅   |
| analytics      | :chart_with_upwards_trend:  | analytics: Add or update analytics or track code.                    | tools       | 📈   |
| CI             | :green_heart:               | CI: fix CI build                                                     | tools       | 💚   |
| insp           | :monocle_face:              | inspect: Data exploration/inspection.                                | tools       | 🧐   |
| init           | :tada:                      | init: begin a project                                                | status      | 🎉   |
| WIP            | :construction:              | WIP: work in progress                                                | status      | 🚧   |
| deploy         | :rocket:                    | deploy: deploy stuff                                                 | status      | 🚀   |
| tag            | :bookmark:                  | tag: release / version tags                                          | status      | 🔖   |
| merge          | :twisted_rightwards_arrows: | merge: Merge branches.                                               | status      | 🔀   |
| pkg            | :package:                   | package: Add or update compiled files or packages.                   | status      | 📦️  |
| conf           | :wrench:                    | conf: Add or update configuration files.                             | config      | 🔧   |
| dev            | :hammer:                    | dev: Add or update development scripts.                              | config      | 🔨   |
| CI-conf        | :construction_worker:       | CI-conf: Add or update CI build system.                              | config      | 👷   |
| depen          | :heavy_plus_sign:           | add dependency: Add a dependency.                                    | dependency  | ➕   |
| rm-depen       | :heavy_minus_sign:          | remove dependency: Remove a dependency.                              | dependency  | ➖   |
| downgrade      | :agrrow_down:               | downgrade: Downgrade dependencies.                                   | dependency  | ⬇️   |
| upgrade        | :arrow_up:                  | upgrade: Upgrade dependencies.                                       | dependency  | ⬆️   |
| pin            | :pushpin:                   | pin: Pin dependencies to specific versions.                          | dependency  | 📌   |
| ext-API        | :alien:                     | external API: Update code due to external API changes.               | dependency  | 👽️  |
| contrib        | :busts_in_silhouette:       | contributor: Add or update contributor(s).                           | real world  | 👥   |
| dev-exp        | :technologist:              | developer: Improve developer experience.                             | real world  | 🧑‍💻   |
| money          | :money_with_wings:          | money: Add sponsorships or money related infrastructure.             | real world  | 💸   |
| bad            | :poop:                      | bad: Write bad code that needs to be improved.                       | trash       | 💩   |
| drunk          | :beers:                     | drunk: Write code drunkenly.                                         | trash       | 🍻   |
| resp           | :iphone:                    | responsive: Work on responsive design.                               | todo        | 📱   |
| mock           | :clown_face:                | mock: Mock things.                                                   | todo        | 🤡   |
| egg            | :egg:                       | egg: Add or update an easter egg.                                    | todo        | 🥚   |
| ignore         | :see_no_evil:               | ignore: Add or update a .gitignore file.                             | todo        | 🙈   |
| snap           | :camera_flash:              | snapshots: Add or update snapshots.                                  | todo        | 📸   |
| expt           | :alembic:                   | experiments: Perform experiments.                                    | todo        | ⚗️   |
| SEO            | :mag:                       | SEO: Improve SEO.                                                    | todo        | 🔍️  |
| error          | :goal_net:                  | errors: Catch errors.                                                | todo        | 🥅   |
| flag           | :triangular_flag_on_post:   | flag: Add, update, or remove feature flags.                          | todo        | 🚩   |
| animation      | :dizzy:                     | animation: Add or update animations and transitions.                 | todo        | 💫   |
| roles          | :passport_control:          | roles: Work on code related to authorization, roles and permissions. | todo        | 🛂   |
| rm-dead        | :coffin:                    | remove dead: Remove dead code.                                       | todo        | ⚰️   |
| fail-test      | :test_tube:                 | fail-test: Add a failing test.                                       | todo        | 🧪   |
| biz            | :necktie:                   | business: Add or update business logic.                              | todo        | 👔   |
| health         | :stethoscope:               | health: Add or update healthcheck.                                   | todo        | 🩺   |
| infrastructure | :bricks:                    | infrastructure: Infrastructure related changes.                      | todo        | 🧱   |
