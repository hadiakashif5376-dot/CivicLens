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
    constants.py rules.py workflow.py security.py config.py errors.py geo.py geocode.py
    db.py models.py schemas.py seed.py
    services/auth.py        register, sign in
    services/complaints.py  submit, queue, assign, move status
  ui/                       Streamlit only. Calls services, never the database.
    bootstrap.py session.py components.py format.py location.py
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
GROQ_API_KEY = "your-groq-key"      # optional, see "AI classification" below
```

Tables are created on the first start. Without `DATABASE_URL` the app falls back to SQLite and shows a "demo storage" warning.

## AI classification (Groq)

When `GROQ_API_KEY` is set, each new complaint is read by a Groq model, which suggests the category, urgency and a one-line summary (`core/ai.py`, `core/services/triage.py`). The officer sees the summary and still confirms or changes the category, urgency and team.

- Without a key, the keyword rules in `core/rules.py` are used. If the call fails or returns something invalid, the rules are used too and the officer screen shows the reason.
- The AI can raise the urgency above the keyword result but never lower it, so a model that underrates a hazard cannot hide it.
- Complaint text is sent to Groq. Say so in your privacy notice before real use.
- `GROQ_MODEL` is optional. The default is `openai/gpt-oss-120b`. `llama-3.3-70b-versatile` and `llama-3.1-8b-instant` are alternatives. Check Groq's model list if a model name stops working.
- A new table, `ai_analyses`, is created automatically on the next start. Existing tables are not changed, and older complaints simply have no AI summary.

## Known limits

- Signing in does not survive a browser refresh.
- No password reset and no rate limiting on sign-in.
- Locations come from a demo list of areas (`core/constants.py`), the browser's location (the citizen must allow it), or typed coordinates. Replace the demo list with your city's list or a geocoder.
- Place names and nearby areas come from OpenStreetMap's free Nominatim and Overpass services (`core/geocode.py`). They are for light use only (about one request per second). For real traffic, run your own geocoder or use a paid one. The citizen's coordinates are sent to these services, which the location screen says.
- The location button uses the `streamlit-geolocation` package, whose last release was in 2023. If it ever breaks, the other two ways of setting a location still work.
- Tables are created with `create_all`. Add Alembic migrations before changing the schema on real data.
- Free hosted databases and apps can pause after a period of inactivity.

## Next steps

1. **Photos.** Add `st.file_uploader` and an `attachments` table, then extend `core/ai.py` to send the photo to a Groq vision model alongside the text. Keep `rules.py` as the fallback.
2. **Voice.** Add `st.audio_input` and a transcription call ahead of the analysis step.
3. **Duplicates and hotspots.** Enable pgvector and PostGIS on Supabase, store an embedding per complaint, and query by similarity within a distance.
4. **Dashboard.** Hotspot rings and a generated summary on the officer screen.
