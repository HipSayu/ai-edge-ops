"""The AlarmSink port: what happens on the spot when someone walks into a zone. Nothing here needs the cloud, so the alarm
sounds when the network is down too.

Three things can be switched on, together: a log line, a command (play a sound, switch a relay on a GPIO pin: whatever
the device offers, given as an argument list, never through a shell) and an HTTP call (a siren or a public-address system
on the site's network)."""

import logging
import os
import subprocess
import threading
import urllib.request
from collections.abc import Sequence

from edge.application.ports import AlarmSink

log = logging.getLogger("edge.alarm")


class LogAlarm:
    def trigger(self, camera_id: int, reason: str) -> None:
        log.warning("ALARM camera %s: %s", camera_id, reason)


class CommandAlarm:
    """Runs a command in the background. While the last run is still going, a new alarm does not start another, so a sound
    of a few seconds is not played over itself. The command learns what happened from PPE_ALARM_CAMERA and PPE_ALARM_ZONE."""

    def __init__(self, command: Sequence[str]) -> None:
        if not command:
            raise ValueError("an alarm command needs at least the program to run")
        self._command = list(command)
        self._running: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def trigger(self, camera_id: int, reason: str) -> None:
        with self._lock:
            if self._running is not None and self._running.poll() is None:
                return
            env = {**os.environ, "PPE_ALARM_CAMERA": str(camera_id), "PPE_ALARM_ZONE": reason}
            self._running = subprocess.Popen(  # noqa: S603 - an argument list, no shell
                self._command, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )


class HttpAlarm:
    """Calls a URL in its own thread, so a slow siren cannot hold up the camera. {camera} and {zone} in the URL are replaced."""

    def __init__(self, url: str, timeout: float = 3.0) -> None:
        if not url.startswith(("http://", "https://")):
            raise ValueError("an alarm URL starts with http:// or https://")
        self._url, self._timeout = url, timeout

    def trigger(self, camera_id: int, reason: str) -> None:
        url = self._url.replace("{camera}", str(camera_id)).replace("{zone}", urllib.request.quote(reason))
        threading.Thread(target=self._call, args=(url,), name="alarm-http", daemon=True).start()

    def _call(self, url: str) -> None:
        try:
            with urllib.request.urlopen(url, timeout=self._timeout):  # noqa: S310 - scheme checked in __init__
                pass
        except Exception as error:
            log.warning("the alarm call to %s failed: %s", url, error)


class MultiAlarm:
    """Several alarms as one. One that fails does not keep the others from sounding."""

    def __init__(self, sinks: Sequence[AlarmSink]) -> None:
        self._sinks = list(sinks)

    def trigger(self, camera_id: int, reason: str) -> None:
        for sink in self._sinks:
            try:
                sink.trigger(camera_id, reason)
            except Exception:
                log.exception("an alarm failed (camera %s)", camera_id)
