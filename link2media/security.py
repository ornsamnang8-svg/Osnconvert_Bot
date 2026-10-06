"""URL validation, SSRF defense, and sanitization utilities."""

from __future__ import annotations

import ipaddress
import re
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse

# Regexp to extract URLs from text
URL_REGEX = re.compile(
    r"""(?i)\b((?:https?://)(?:[^\s<>"'{}|\\^`\[\]]+))""",
    re.VERBOSE,
)

# Explicit allowed domain suffixes for targeted platforms
# Subdomains like www., m., vm., vt., mobile. will be matched properly
PLATFORM_DOMAINS: dict[str, set[str]] = {
    "YouTube": {
        "youtube.com",
        "youtu.be",
        "m.youtube.com",
        "music.youtube.com",
        "www.youtube.com",
    },
    "TikTok": {
        "tiktok.com",
        "www.tiktok.com",
        "vm.tiktok.com",
        "vt.tiktok.com",
        "m.tiktok.com",
    },
    "Facebook": {
        "facebook.com",
        "www.facebook.com",
        "m.facebook.com",
        "web.facebook.com",
        "fb.watch",
        "fb.com",
    },
    "Instagram": {
        "instagram.com",
        "www.instagram.com",
        "instagr.am",
    },
    "X/Twitter": {
        "twitter.com",
        "www.twitter.com",
        "mobile.twitter.com",
        "x.com",
        "www.x.com",
        "mobile.x.com",
        "t.co",
    },
}

# Dangerous IP networks (Private, loopback, link-local, cloud metadata, etc.)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),  # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local & AWS/GCP/Azure metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),  # Private
    ipaddress.ip_network("192.0.0.0/24"),  # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1
    ipaddress.ip_network("192.88.99.0/24"),  # 6to4 Relay Anycast
    ipaddress.ip_network("192.168.0.0/16"),  # Private
    ipaddress.ip_network("198.18.0.0/15"),  # Network benchmark
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved
    ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
    # IPv6
    ipaddress.ip_network("::1/128"),  # Loopback
    ipaddress.ip_network("::/128"),  # Unspecified
    ipaddress.ip_network("::ffff:0:0/96"),  # IPv4-mapped
    ipaddress.ip_network("100::/64"),  # Discard prefix
    ipaddress.ip_network("2001:db8::/32"),  # Documentation
    ipaddress.ip_network("fc00::/7"),  # Unique local
    ipaddress.ip_network("fe80::/10"),  # Link-local
    ipaddress.ip_network("ff00::/8"),  # Multicast
]


def extract_urls(text: str) -> list[str]:
    """Find all HTTP/HTTPS URLs in text, stripping trailing punctuation."""
    matches = URL_REGEX.findall(text)
    clean_urls: list[str] = []
    for match in matches:
        url = match.strip()
        # Clean trailing brackets or punctuation often added in chat
        url = re.sub(r"[.,;:!?)\]>]+$", "", url)
        if url:
            clean_urls.append(url)
    return clean_urls


def is_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address belongs to any blocked or non-public network."""
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return True
    for network in BLOCKED_IP_NETWORKS:
        if ip in network:
            return True
    return False


def validate_hostname_ssrf(hostname: str) -> bool:
    """
    Resolve hostname and verify that NONE of the resolved IP addresses
    belong to private, loopback, link-local, or cloud metadata ranges.
    """
    clean_host = hostname.strip().strip("[]")
    if not clean_host:
        return False

    # Check if host is direct IP literal
    try:
        ip = ipaddress.ip_address(clean_host)
        return not is_ip_blocked(ip)
    except ValueError:
        pass

    # Resolve via DNS
    try:
        addr_info = socket.getaddrinfo(clean_host, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
        if not addr_info:
            return False
        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if is_ip_blocked(ip):
                return False
        return True
    except (socket.gaierror, socket.herror, OSError):
        return False


def identify_platform(hostname: str) -> Optional[str]:
    """Match hostname against approved platform domains."""
    host = hostname.lower().strip()
    for platform, domains in PLATFORM_DOMAINS.items():
        for d in domains:
            if host == d or host.endswith("." + d):
                return platform
    return None


def validate_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate URL structure, approved platform, and SSRF security.
    Returns: (is_valid, platform_name_or_none, error_key_or_none)
    """
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False, None, "invalid_url"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, None, "invalid_url"

    hostname = parsed.hostname
    if not hostname:
        return False, None, "invalid_url"

    platform = identify_platform(hostname)
    if not platform:
        return False, None, "unsupported_platform"

    # Fast path: check for obvious playlist/channel/live links where possible
    path = parsed.path.lower()
    query = parsed.query.lower()

    if platform == "YouTube":
        # Disallow playlist directly if it is purely a playlist URL (/playlist?list=...)
        if "/playlist" in path and "list=" in query:
            return False, platform, "err_playlist"
        if path.startswith(("/channel/", "/c/", "/user/")):
            return False, platform, "unsupported_link"

    # SSRF DNS Check
    if not validate_hostname_ssrf(hostname):
        return False, platform, "blocked_destination"

    return True, platform, None


def sanitize_filename(name: str, max_length: int = 80) -> str:
    """Sanitize title or filename for safe local disk storage."""
    # Strip null bytes and control chars
    clean = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", name)
    # Replace dangerous filesystem characters
    clean = re.sub(r'[<>:"/\\|?*]', "_", clean)
    # Collapse consecutive spaces/underscores
    clean = re.sub(r"[\s_]+", "_", clean).strip("._ ")
    if not clean:
        clean = "media"
    if len(clean) > max_length:
        clean = clean[:max_length].rstrip("._ ")
    return clean
