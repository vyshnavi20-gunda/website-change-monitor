"""Official sources to monitor.  Add one object to support another company."""

SITES = (
    {
        "company": "Norsk Hydro",
        "url": "https://www.hydro.com/",
        "sections": (
            "https://www.hydro.com/en/global/media/news/",
            "https://www.hydro.com/en/global/investors/",
        ),
    },
    {
        "company": "Constellium",
        "url": "https://www.constellium.com/",
        "sections": (
            "https://www.constellium.com/news",
            "https://www.constellium.com/investors",
        ),
    },
    {
        "company": "Alcoa",
        "url": "https://www.alcoa.com/",
        # Alcoa publishes corporate releases on this official subdomain.
        "sections": (
            "https://news.alcoa.com/press-releases/default.aspx",
            "https://investors.alcoa.com/",
            "https://www.alcoa.com/global/en/stories",
        ),
        "allowed_hosts": ("www.alcoa.com", "alcoa.com", "news.alcoa.com", "investors.alcoa.com"),
    },
    {
        "company": "Ma'aden",
        "url": "https://www.maaden.com/",
        "sections": (
            "https://www.maaden.com/news",
            "https://www.maaden.com/investor-relations",
        ),
    },
    {
        "company": "Rio Tinto",
        "url": "https://www.riotinto.com/",
        "sections": (
            "https://www.riotinto.com/news/releases",
            "https://www.riotinto.com/invest",
            "https://www.riotinto.com/news",
        ),
    },
)
