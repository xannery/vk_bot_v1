from typing import Optional
from urllib.parse import urlparse, urlunparse


ALLOWED_DOMAINS = {
    "vk.com": "vk",
    "vk.ru": "vk",
    "t.me": "telegram",
    "telegram.me": "telegram",
    "instagram.com": "instagram",
    "tiktok.com": "tiktok",
    "twitch.tv": "twitch",
}


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    netloc = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.rstrip("/")
    return urlunparse(("https", netloc, path, "", "", ""))


def get_platform(url: str) -> Optional[str]:
    netloc = urlparse(url).netloc.lower().replace("www.", "")
    for domain, name in ALLOWED_DOMAINS.items():
        if domain in netloc:
            return name
    return None