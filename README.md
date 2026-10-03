# CivicLens

A Streamlit app where citizens report city problems and officers review, assign and track them. This is step 1, the core loop with no AI. Keyword rules from the original prototype give a **suggested** category and urgency. The officer's confirmed values are stored separately, so you can measure later how often the suggestion was right.

Two roles, one screen each:

- **Citizen:** sends a complaint (description plus location) and follows its progress and timeline.
- **Officer:** sees a map and queue, verifies the suggested details, assigns a team, and moves the complaint to in progress and resolved.

## Structure

```
streamlit_app.py            entry point (set this as the main file on Streamlit Cloud)
civiclens/
  core/                     all the logic. Never imports Streamlit.
    constants.py rules.py workflow.py security.py config.py errors.py
    db.py models.py schemas.py seed.py
    services/auth.py        register, sign in
    services/complaints.py  submit, queue, assign, move status
  ui/                       Streamlit only. Calls services, never the database.
    bootstrap.py session.py components.py format.py
    pages/login.py citizen.py officer.py
tests/
.streamlit/
  config.toml
  secrets.toml.example
```

The rule that keeps it modular: **pages call services, services own the database**. `tests/test_architecture.py` fails if a page imports SQLAlchemy or the database layer, or if `core` imports Streamlit. New features (photo analysis, duplicate detection) become new services that the same pages call.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml     # then edit it
streamlit run streamlit_app.py
pytest
```

There is no default officer account, because this repository will be public. Set `OFFICER_EMAIL` and `OFFICER_PASSWORD` in `secrets.toml`, and the account is created on first start. Citizens register themselves from the sign-in page.

## Deploy: GitHub, Supabase, Streamlit Community Cloud

Streamlit Community Cloud wipes its disk when an app restarts, so a SQLite file will not keep your data. Use a hosted Postgres database.

1. **GitHub.** Push this folder to a repository. `.streamlit/secrets.toml` is git-ignored. Never commit it.
2. **Supabase.** Create a project and copy its database connection string. Use the pooler string, which works over IPv4. If the password contains symbols, percent-encode them (`@` becomes `%40`). Supabase also has PostGIS and pgvector, which steps 3 and 4 need.
3. **Streamlit Community Cloud.** Create a new app from your repository, pick the branch, and set the main file to `streamlit_app.py`. In the advanced settings, paste your secrets:

```toml
DATABASE_URL = "postgresql://postgres.PROJECTREF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres"
OFFICER_EMAIL = "you@example.com"
OFFICER_PASSWORD = "a-strong-password"
DISPLAY_TZ = "Asia/Karachi"
```

Tables are created on the first start. Without `DATABASE_URL` the app falls back to SQLite and shows a "demo storage" warning.

## Known limits

- Signing in does not survive a browser refresh.
- No password reset and no rate limiting on sign-in.
- Locations come from a demo list of areas (`core/constants.py`) or typed coordinates. Replace with your city's list or a geocoder.
- Tables are created with `create_all`. Add Alembic migrations before changing the schema on real data.
- Free hosted databases and apps can pause after a period of inactivity.

## Next steps

1. **Photos and AI classification.** Add `st.file_uploader` and an `attachments` table, then a `core/services/analysis.py` that sends text and photo to an LLM and returns structured JSON. Keep `rules.py` as the fallback if the call fails. Put the API key in secrets.
2. **Voice.** Add `st.audio_input` and a transcription call ahead of the analysis step.
3. **Duplicates and hotspots.** Enable pgvector and PostGIS on Supabase, store an embedding per complaint, and query by similarity within a distance.
4. **Dashboard.** Hotspot rings and a generated summary on the officer screen.
