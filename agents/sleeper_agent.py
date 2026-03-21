"""Sleeper API agent — fetches player stats and trending data."""
import requests
import config


class SleeperAgent:
    """Thin wrapper around the public Sleeper fantasy API."""

    def __init__(self, base_url: str = config.SLEEPER_BASE_URL) -> None:
        self._base = base_url.rstrip("/")
        self._session = requests.Session()
        self._players_cache: dict | None = None

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_top_performers(
        self, season: int, week: int, top_n: int = 20
    ) -> list[dict]:
        """Return the top-N fantasy performers for a given week.

        Each item is the raw stats dict from Sleeper with an added
        ``player_id`` key, sorted descending by ``pts_ppr``.
        """
        url = f"{self._base}/stats/nfl/regular/{season}/{week}"
        data: dict = self._get(url)

        players = []
        for player_id, stats in data.items():
            entry = dict(stats)
            entry["player_id"] = player_id
            players.append(entry)

        players.sort(key=lambda p: p.get("pts_ppr", 0.0), reverse=True)
        return players[:top_n]

    def get_player_info(self, player_id: str) -> dict:
        """Return metadata for a single player by Sleeper player_id.

        Raises ValueError if the player is not found.
        """
        all_players = self._all_players()
        if player_id not in all_players:
            raise ValueError(f"Player not found in Sleeper roster: {player_id}")
        return all_players[player_id]

    def get_trending_players(self, lookback_hours: int = 24) -> list[dict]:
        """Return trending add players from Sleeper over the last N hours."""
        url = f"{self._base}/players/nfl/trending/add"
        params = {"lookback_hours": lookback_hours, "limit": 50}
        return self._get(url, params=params)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _all_players(self) -> dict:
        """Fetch (and cache) the full Sleeper player database."""
        if self._players_cache is None:
            url = f"{self._base}/players/nfl"
            self._players_cache = self._get(url)
        return self._players_cache

    def _get(self, url: str, params: dict | None = None) -> dict | list:
        resp = self._session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
