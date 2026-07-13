# Aureon Watch (static PWA)

**Source of truth:** `aureon/operator/wearable/`.
This directory is a verbatim copy so the production nginx frontend serves the
watch app at `/watch/` (same origin as the `/api` proxy), in addition to the
operator serving it directly at `GET /watch`.

To update: edit `aureon/operator/wearable/*`, then copy the files here.
Do not edit this copy directly.
