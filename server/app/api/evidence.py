"""HTTP delivery for already ownership-checked evidence artifacts."""
from __future__ import annotations

import json

from fastapi import HTTPException
from fastapi.responses import Response, StreamingResponse

from app.config import REPO_ROOT, get_settings
from app.results.artifacts import (
    ArtifactNotFound,
    ArtifactTooLarge,
    ResolvedArtifact,
    enforce_size,
    revalidate,
)
from app.results.redaction import Redactor


_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "private, no-store",
}


def artifact_response(artifact: ResolvedArtifact, *, download: bool):
    try:
        artifact = revalidate(artifact)
        enforce_size(artifact, download=download)
    except ArtifactNotFound as exc:
        raise HTTPException(404, "artifact unavailable") from exc
    except ArtifactTooLarge as exc:
        raise HTTPException(413, str(exc)) from exc

    settings = get_settings()
    redactor = Redactor.from_environment(private_paths=(
        artifact.private_root,
        settings.outputs_dir,
        settings.data_dir,
        REPO_ROOT,
    ))
    disposition = "attachment" if download else "inline"
    headers = {
        **_HEADERS,
        "Content-Disposition": f'{disposition}; filename="{artifact.filename}"',
    }

    # Parse JSON before response headers are sent, so malformed structured
    # evidence fails deterministically rather than truncating a 200 response.
    if artifact.media_type == "application/json":
        try:
            content = redactor.json_bytes(artifact.path)
        except (json.JSONDecodeError, UnicodeError, OSError) as exc:
            raise HTTPException(422, "malformed JSON evidence") from exc
        return Response(content=content, media_type=artifact.media_type, headers=headers)

    return StreamingResponse(
        redactor.iter_file(
            artifact.path,
            artifact.media_type,
            settings.evidence.stream_chunk_bytes,
        ),
        media_type=artifact.media_type,
        headers=headers,
    )