import logging

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, StreamingResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from trace_id import REQUEST_ID_HEADER, RequestContextFilter, RequestLogMiddleware, get_request_id, outgoing_headers


async def echo(request):
    return PlainTextResponse(get_request_id() or "none")


async def missing(request):
    return PlainTextResponse("no", status_code=404)


async def boom(request):
    raise RuntimeError("kaput")


async def health(request):
    return PlainTextResponse("ok")


async def stream(request):
    async def chunks():
        yield b"a"
        yield b"b"

    return StreamingResponse(chunks())


async def downstream(request):
    return PlainTextResponse(outgoing_headers().get(REQUEST_ID_HEADER, "none"))


@pytest.fixture
def client():
    routes = [
        Route(path, handler)
        for path, handler in [
            ("/echo", echo),
            ("/missing", missing),
            ("/boom", boom),
            ("/api/health", health),
            ("/stream", stream),
            ("/downstream", downstream),
        ]
    ]
    app = Starlette(routes=routes)
    app.add_middleware(RequestLogMiddleware, service="test")
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def lines(caplog):
    return [r for r in caplog.records if r.name == "trace_id"]


def test_makes_an_id_and_returns_it(client):
    r = client.get("/echo")
    assert r.headers[REQUEST_ID_HEADER] == r.text != "none"
    assert len(r.text) == 32


def test_the_id_is_gone_after_the_request(client):
    client.get("/echo")
    assert get_request_id() is None and outgoing_headers() == {}


def test_keeps_the_callers_id_so_it_follows_the_call_across_services(client):
    r = client.get("/echo", headers={REQUEST_ID_HEADER: "web-123.abc"})
    assert r.text == r.headers[REQUEST_ID_HEADER] == "web-123.abc"
    assert client.get("/downstream", headers={REQUEST_ID_HEADER: "web-123.abc"}).text == "web-123.abc"


@pytest.mark.parametrize("bad", ["has space", "x" * 65, "semi;colon", "tab\there"])
def test_replaces_an_id_that_is_not_safe_to_log(client, bad):
    r = client.get("/echo", headers={REQUEST_ID_HEADER: bad})
    assert r.text != bad and len(r.text) == 32


def test_logs_one_line_per_request_with_the_result(client, caplog):
    caplog.set_level(logging.INFO)
    client.get("/echo?token=secret")
    (record,) = lines(caplog)
    assert (record.http_method, record.http_path, record.http_status) == ("GET", "/echo", 200)
    assert record.levelno == logging.INFO and record.duration_ms >= 0
    assert "secret" not in record.getMessage()  # the query string never reaches the log


def test_level_follows_the_status(client, caplog):
    caplog.set_level(logging.INFO)
    client.get("/missing")
    assert lines(caplog)[-1].levelno == logging.WARNING


def test_unhandled_error_is_logged_with_traceback_and_answers_500(client, caplog):
    caplog.set_level(logging.INFO)
    assert client.get("/boom").status_code == 500
    record = lines(caplog)[-1]
    assert record.levelno == logging.ERROR and record.http_status == 500 and record.exc_info


def test_health_probes_are_not_logged(client, caplog):
    caplog.set_level(logging.INFO)
    client.get("/api/health")
    assert lines(caplog) == []


def test_streamed_response_is_logged_once_it_has_ended(client, caplog):
    caplog.set_level(logging.INFO)
    assert client.get("/stream").text == "ab"
    assert len(lines(caplog)) == 1


def test_filter_puts_service_and_id_on_every_record():
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None)
    RequestContextFilter("svc").filter(record)
    assert (record.service, record.request_id) == ("svc", "-")
