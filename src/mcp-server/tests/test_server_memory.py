"""Tests for server.py memory management: in-flight guard, jobdone mode, unload tool.

EasyOCR-free by design (like the rest of the suite): server.py imports EasyOCR
lazily, so importing the module and exercising the unload machinery never pulls
in PyTorch. Tests manipulate module globals directly and restore them.
"""

import pytest

import server


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    monkeypatch.delenv("EASYOCR_UNLOAD_TIMEOUT", raising=False)
    monkeypatch.delenv("EASYOCR_UNLOAD_JOBDONE", raising=False)
    with server._reader_lock:
        server._reader_cache.clear()
        server._in_flight = 0
        server._unload_when_idle = False
    server._cancel_unload_timer()
    yield
    with server._reader_lock:
        server._reader_cache.clear()
        server._in_flight = 0
        server._unload_when_idle = False
    server._cancel_unload_timer()


def test_unload_readers_frees_cache():
    server._reader_cache[("en",)] = object()
    server._reader_cache[("ch_tra", "en")] = object()
    assert server._unload_readers() == 2
    assert not server._reader_cache


def test_unload_readers_skips_while_in_flight():
    server._reader_cache[("en",)] = object()
    server._in_flight = 1
    assert server._unload_readers() == 0
    assert server._reader_cache


def test_unload_tool_reports_freed_count():
    server._reader_cache[("en",)] = object()
    assert "Unloaded 1" in server.unload_ocr_models()
    assert "Unloaded 0" in server.unload_ocr_models()


def test_unload_tool_defers_while_in_flight():
    server._reader_cache[("en",)] = object()
    server._in_flight = 1
    message = server.unload_ocr_models()
    assert "in progress" in message.lower()
    assert server._reader_cache
    server._job_done()
    assert not server._reader_cache
    assert server._unload_when_idle is False


def test_job_start_disarms_pending_timer(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "300")
    server._schedule_unload()
    assert server._unload_timer is not None
    server._job_start()
    assert server._unload_timer is None
    server._job_done()


def test_job_done_rearms_timer_when_idle(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "300")
    server._job_start()
    server._job_done()
    assert server._in_flight == 0
    assert server._unload_timer is not None


def test_job_done_does_not_rearm_while_others_in_flight(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "300")
    server._job_start()
    server._job_start()
    server._job_done()
    assert server._in_flight == 1
    assert server._unload_timer is None
    server._job_done()
    assert server._unload_timer is not None


def test_jobdone_mode_unloads_after_call(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_JOBDONE", "1")
    server._reader_cache[("en",)] = object()
    server._job_start()
    server._job_done()
    assert not server._reader_cache
    assert server._unload_timer is None


def test_jobdone_mode_waits_for_all_calls(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_JOBDONE", "1")
    server._reader_cache[("en",)] = object()
    server._job_start()
    server._job_start()
    server._job_done()
    assert server._reader_cache
    server._job_done()
    assert not server._reader_cache


def test_run_ocr_resets_in_flight_on_failure(monkeypatch):
    def boom(languages):
        raise ValueError("reader init failed")

    monkeypatch.setattr(server, "get_reader", boom)
    with pytest.raises(ValueError):
        server._run_ocr("dummy.png", detail=1, paragraph=False, width_ths=0.7, height_ths=0.7)
    assert server._in_flight == 0


def test_schedule_unload_disabled_when_timeout_zero(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "0")
    server._schedule_unload()
    assert server._unload_timer is None
