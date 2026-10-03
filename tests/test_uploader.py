import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules import uploader


class FakeResponse:
    def __init__(self, status):
        self.status = status


class FakeHttpError(Exception):
    def __init__(self, status):
        super().__init__(f"HTTP {status}")
        self.resp = FakeResponse(status)


class FakeRequest:
    def __init__(self, failures, status=503):
        self.failures = failures
        self.status = status
        self.calls = 0

    def next_chunk(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise FakeHttpError(self.status)
        return (None, {"id": "vid-123"})


def test_resumable_upload_retries_transient_errors_and_resumes():
    request = FakeRequest(failures=2)
    result = uploader._resumable_upload(request, max_retries=5, base_delay=0)
    assert result == {"id": "vid-123"}
    assert request.calls == 3


def test_resumable_upload_gives_up_after_max_retries():
    request = FakeRequest(failures=99)
    with pytest.raises(FakeHttpError):
        uploader._resumable_upload(request, max_retries=2, base_delay=0)
    assert request.calls == 3


def test_resumable_upload_does_not_retry_auth_errors():
    request = FakeRequest(failures=1, status=403)
    with pytest.raises(FakeHttpError):
        uploader._resumable_upload(request, max_retries=5, base_delay=0)
    assert request.calls == 1


def test_is_retryable_classifies_network_errors():
    assert uploader._is_retryable(FakeHttpError(503))
    assert uploader._is_retryable(ConnectionError("reset"))
    assert not uploader._is_retryable(FakeHttpError(403))
    assert not uploader._is_retryable(ValueError("bad input"))


def test_uploader_no_longer_uses_pickle():
    assert "pickle" not in inspect.getsource(uploader)


def test_upload_uses_chunked_resumable_transfer():
    assert uploader.UPLOAD_CHUNK_SIZE > 0
