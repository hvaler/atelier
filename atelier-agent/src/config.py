"""Configuration settings for Atelier Agent."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Atelier Agent"
    app_version: str = "0.1.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    gcp_project: str = os.getenv("GCP_PROJECT", "atelier-hack")
    gcp_location: str = os.getenv("GCP_LOCATION", "europe-west3")
    firestore_db: str = os.getenv("FIRESTORE_DATABASE", "(default)")
    inbox_bucket: str = os.getenv("INBOX_BUCKET", "atelier-hack-inbox")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    #: Where the *model* lives, which is not where the *service* lives.
    #:
    #: These were the same variable, and `deploy.sh` set it from the Cloud Run region. The
    #: service runs in europe-west1, where `gemini-3.5-flash` is not published: every call in
    #: production returned `404 NOT_FOUND` and fell into the deterministic template, invisibly,
    #: because the failure was swallowed. The mandatory "Gemini 3.5 or newer" requirement was
    #: met by the code and broken by the deployment.
    #:
    #: europe-west3 rather than `global`: both serve the model, and west3 keeps a student's
    #: drawings inside the EU and co-located with the Firestore database (eur3).
    gemini_location: str = os.getenv("GEMINI_LOCATION", "europe-west3")

    #: The routing model, and the key that reaches it.
    #:
    #: Gemma is not published on Vertex AI — `gemma-3-*-it` and `gemma-4-*` all return 404 there,
    #: and reaching one would need a billed Model Garden endpoint. It *is* hosted on the Gemini
    #: API, which authenticates with an API key rather than ADC. That is the only reason this
    #: project has a second credential path; it is scoped to one call and read from Secret
    #: Manager, never committed.
    #:
    #: Verified on this key: gemma-4-26b-a4b-it answers a structured routing prompt in ~1.6s,
    #: four times out of four. Its vision path does not work — it spends the whole output budget
    #: reasoning and returns empty, and at larger budgets it hangs for minutes. So Gemma reads
    #: words and `gemini_model` looks at pictures.
    router_model: str = os.getenv("ROUTER_MODEL", "gemma-4-26b-a4b-it")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")

    #: Where student memory lives. Firestore in production, dicts everywhere else.
    #:
    #: Explicit rather than inferred from whether credentials happen to be present: a service
    #: that silently downgrades to process memory is a service that loses a student's history on
    #: the next cold start and reports nothing. CI and local development run on "memory" by
    #: default and say so on /api/health.
    memory_backend: str = os.getenv(
        "MEMORY_BACKEND", "firestore" if os.getenv("ENVIRONMENT") == "production" else "memory"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
