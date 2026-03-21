"""Reddit research agent — scrapes trending player mentions using PRAW."""
import praw
import config


class RedditAgent:
    """Scrapes r/fantasyfootball (and related subs) for player mention counts."""

    DEFAULT_SUBREDDITS = ["fantasyfootball", "nfl"]

    def __init__(
        self,
        client_id: str = config.REDDIT_CLIENT_ID,
        client_secret: str = config.REDDIT_CLIENT_SECRET,
        user_agent: str = config.REDDIT_USER_AGENT,
    ) -> None:
        self._reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_trending_mentions(
        self,
        player_names: list[str],
        subreddits: list[str] | None = None,
        post_limit: int = 100,
    ) -> list[dict]:
        """Return mention counts for each player across hot posts.

        Returns a list of dicts sorted by ``mention_count`` descending::

            [{"player_name": "Josh Allen", "mention_count": 12}, ...]
        """
        if not player_names:
            return []

        subs = subreddits or self.DEFAULT_SUBREDDITS
        titles = self._collect_titles(subs, post_limit)

        results = []
        for name in player_names:
            name_lower = name.lower()
            count = sum(1 for t in titles if name_lower in t.lower())
            results.append({"player_name": name, "mention_count": count})

        results.sort(key=lambda r: r["mention_count"], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_titles(self, subreddits: list[str], limit: int) -> list[str]:
        """Collect post titles from the given subreddits."""
        titles: list[str] = []
        for sub_name in subreddits:
            sub = self._reddit.subreddit(sub_name)
            for post in sub.hot(limit=limit):
                titles.append(post.title)
        return titles
