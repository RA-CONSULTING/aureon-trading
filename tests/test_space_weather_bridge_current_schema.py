from __future__ import annotations

from aureon.data_feeds import aureon_space_weather_bridge as sw


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_space_weather_bridge_parses_current_swpc_kp_schema(monkeypatch):
    bridge = sw.SpaceWeatherBridge()

    monkeypatch.setattr(
        sw.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(
            [{"time_tag": "2026-07-13T18:00:00", "Kp": 3.67}]
        ),
    )

    assert bridge._fetch_kp_index() == {"current_kp": 3.67}


def test_space_weather_bridge_parses_current_swpc_wind_and_mag_schema(monkeypatch):
    bridge = sw.SpaceWeatherBridge()

    def fake_get(url, *args, **kwargs):
        if "rtsw_wind" in url:
            return FakeResponse(
                [
                    {
                        "time_tag": "2026-07-14T00:01:00",
                        "proton_speed": 423.51,
                        "proton_density": 2.64,
                    }
                ]
            )
        if "rtsw_mag" in url:
            return FakeResponse(
                [{"time_tag": "2026-07-14T00:01:00", "bz_gsm": 2.15}]
            )
        raise AssertionError(url)

    monkeypatch.setattr(sw.requests, "get", fake_get)

    assert bridge._fetch_solar_wind() == {
        "density": 2.64,
        "speed": 423.51,
        "bz": 2.15,
    }


def test_space_weather_bridge_parses_current_swpc_forecast_schema(monkeypatch):
    bridge = sw.SpaceWeatherBridge()

    monkeypatch.setattr(
        sw.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(
            [
                {"time_tag": "2026-07-14T00:00:00", "kp": 1.67},
                {"time_tag": "2026-07-14T03:00:00", "kp": 5.0},
            ]
        ),
    )

    assert bridge._fetch_3day_forecast() == {"highest_kp_category": "Active"}
