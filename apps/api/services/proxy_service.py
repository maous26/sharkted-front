"""
Service de gestion des proxies rotatifs
Supporte Webshare et autres fournisseurs
Utilisé par tous les scrapers (Vinted, Nike, Adidas, etc.)
"""

import aiohttp
import httpx
import random
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger

from config import settings


# User agents réalistes pour rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def get_random_user_agent() -> str:
    """Retourne un User-Agent aléatoire"""
    return random.choice(USER_AGENTS)


@dataclass
class Proxy:
    """Représente un proxy"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    last_used: Optional[datetime] = None
    fail_count: int = 0

    @property
    def url(self) -> str:
        """Retourne l'URL du proxy formatée"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"

    def mark_used(self):
        """Marque le proxy comme utilisé"""
        self.last_used = datetime.utcnow()

    def mark_failed(self):
        """Marque une erreur sur ce proxy"""
        self.fail_count += 1


class ProxyRotator:
    """
    Gestionnaire de proxies rotatifs
    - Charge les proxies depuis Webshare ou une liste
    - Rotation automatique entre les proxies
    - Gestion des erreurs et blacklist temporaire
    """

    def __init__(
        self,
        webshare_api_url: Optional[str] = None,
        proxy_list: Optional[List[str]] = None,
        max_fails: int = 3,
        cooldown_minutes: int = 5
    ):
        self.webshare_api_url = webshare_api_url
        self.proxies: List[Proxy] = []
        self.max_fails = max_fails
        self.cooldown_minutes = cooldown_minutes
        self._lock = asyncio.Lock()
        self._initialized = False

        # Charger depuis une liste statique si fournie
        if proxy_list:
            self._load_from_list(proxy_list)

    def _load_from_list(self, proxy_list: List[str]):
        """Charge les proxies depuis une liste de strings"""
        for proxy_str in proxy_list:
            try:
                # Format: host:port:username:password ou host:port
                parts = proxy_str.strip().split(":")
                if len(parts) >= 4:
                    self.proxies.append(Proxy(
                        host=parts[0],
                        port=int(parts[1]),
                        username=parts[2],
                        password=parts[3]
                    ))
                elif len(parts) == 2:
                    self.proxies.append(Proxy(
                        host=parts[0],
                        port=int(parts[1])
                    ))
            except Exception as e:
                logger.warning(f"Failed to parse proxy: {proxy_str} - {e}")

        logger.info(f"Loaded {len(self.proxies)} proxies from list")

    async def initialize(self):
        """Initialise le rotateur en chargeant les proxies"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            if self.webshare_api_url:
                await self._load_from_webshare()

            self._initialized = True
            logger.info(f"ProxyRotator initialized with {len(self.proxies)} proxies")

    async def _load_from_webshare(self):
        """Charge les proxies depuis l'API Webshare"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.webshare_api_url) as response:
                    if response.status == 200:
                        text = await response.text()
                        lines = text.strip().split("\n")

                        for line in lines:
                            try:
                                # Format Webshare: host:port:username:password
                                parts = line.strip().split(":")
                                if len(parts) >= 4:
                                    self.proxies.append(Proxy(
                                        host=parts[0],
                                        port=int(parts[1]),
                                        username=parts[2],
                                        password=parts[3]
                                    ))
                                elif len(parts) == 2:
                                    self.proxies.append(Proxy(
                                        host=parts[0],
                                        port=int(parts[1])
                                    ))
                            except Exception as e:
                                logger.warning(f"Failed to parse proxy line: {line} - {e}")

                        logger.info(f"Loaded {len(self.proxies)} proxies from Webshare")
                    else:
                        logger.error(f"Failed to fetch Webshare proxies: {response.status}")
        except Exception as e:
            logger.error(f"Error loading Webshare proxies: {e}")

    def _get_available_proxies(self) -> List[Proxy]:
        """Retourne les proxies disponibles (non en cooldown)"""
        now = datetime.utcnow()
        cooldown_threshold = now - timedelta(minutes=self.cooldown_minutes)

        available = []
        for proxy in self.proxies:
            # Skip si trop d'erreurs récentes
            if proxy.fail_count >= self.max_fails:
                if proxy.last_used and proxy.last_used > cooldown_threshold:
                    continue
                # Reset après cooldown
                proxy.fail_count = 0

            available.append(proxy)

        return available

    def get_random_proxy(self) -> Optional[Proxy]:
        """Retourne un proxy aléatoire parmi ceux disponibles"""
        available = self._get_available_proxies()

        if not available:
            logger.warning("No available proxies!")
            return None

        # Préférer les proxies moins utilisés récemment
        available.sort(key=lambda p: p.last_used or datetime.min)

        # Prendre parmi les moins utilisés avec un peu de randomisation
        pool_size = min(5, len(available))
        proxy = random.choice(available[:pool_size])
        proxy.mark_used()

        return proxy

    def get_proxy_url(self) -> Optional[str]:
        """Retourne l'URL d'un proxy aléatoire"""
        proxy = self.get_random_proxy()
        return proxy.url if proxy else None

    def report_failure(self, proxy_url: str):
        """Signale une erreur sur un proxy"""
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                proxy.mark_failed()
                logger.warning(f"Proxy {proxy.host}:{proxy.port} failed ({proxy.fail_count}/{self.max_fails})")
                break

    def get_stats(self) -> Dict:
        """Retourne les statistiques des proxies"""
        available = self._get_available_proxies()
        return {
            "total": len(self.proxies),
            "available": len(available),
            "failed": len(self.proxies) - len(available),
        }


# Instance globale du rotateur
_proxy_rotator: Optional[ProxyRotator] = None


async def get_proxy_rotator() -> ProxyRotator:
    """Retourne l'instance globale du proxy rotator"""
    global _proxy_rotator

    if _proxy_rotator is None:
        # URL Webshare depuis les settings ou variable d'environnement
        webshare_url = getattr(settings, 'WEBSHARE_PROXY_URL', None) or settings.PROXY_URL

        _proxy_rotator = ProxyRotator(
            webshare_api_url=webshare_url if webshare_url and "webshare" in webshare_url else None
        )

        # Si c'est une URL simple (pas Webshare), l'ajouter comme proxy unique
        if webshare_url and "webshare" not in webshare_url:
            _proxy_rotator._load_from_list([webshare_url])

        await _proxy_rotator.initialize()

    return _proxy_rotator


async def get_rotating_proxy() -> Optional[str]:
    """Helper pour obtenir un proxy rotatif"""
    if not settings.USE_ROTATING_PROXY:
        return None
    rotator = await get_proxy_rotator()
    return rotator.get_proxy_url()


def get_httpx_client_kwargs(timeout: float = 30.0, use_proxy: bool = True) -> Dict[str, Any]:
    """
    Retourne les kwargs pour créer un httpx.AsyncClient avec proxy si activé.

    Args:
        timeout: Timeout en secondes
        use_proxy: Si True, utilise un proxy si disponible

    Returns:
        Dict avec les kwargs pour httpx.AsyncClient
    """
    kwargs: Dict[str, Any] = {
        "timeout": timeout,
        "follow_redirects": True,
        "headers": {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    }

    if use_proxy and settings.USE_ROTATING_PROXY and _proxy_rotator:
        proxy_url = _proxy_rotator.get_proxy_url()
        if proxy_url:
            kwargs["proxy"] = proxy_url
            logger.debug(f"Utilisation proxy pour requête")

    return kwargs


def get_playwright_proxy_config() -> Optional[Dict[str, str]]:
    """
    Retourne la config proxy pour Playwright.

    Returns:
        Dict avec la config proxy ou None si désactivé
    """
    if not settings.USE_ROTATING_PROXY or not _proxy_rotator:
        return None

    proxy = _proxy_rotator.get_random_proxy()
    if not proxy:
        return None

    if proxy.username and proxy.password:
        return {
            "server": f"{proxy.protocol}://{proxy.host}:{proxy.port}",
            "username": proxy.username,
            "password": proxy.password,
        }
    else:
        return {"server": proxy.url}


async def create_httpx_client_with_proxy(timeout: float = 30.0) -> httpx.AsyncClient:
    """
    Crée un httpx.AsyncClient avec proxy si activé.

    Args:
        timeout: Timeout en secondes

    Returns:
        Instance de httpx.AsyncClient configurée
    """
    # S'assurer que le rotator est initialisé
    if settings.USE_ROTATING_PROXY:
        await get_proxy_rotator()

    kwargs = get_httpx_client_kwargs(timeout=timeout)
    return httpx.AsyncClient(**kwargs)


def get_default_headers(for_api: bool = False, referer: Optional[str] = None) -> Dict[str, str]:
    """
    Retourne les headers par défaut pour les requêtes.

    Args:
        for_api: True pour les requêtes API (JSON), False pour HTML
        referer: URL de referer optionnelle

    Returns:
        Dict des headers
    """
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
    }

    if for_api:
        headers["Accept"] = "application/json, text/plain, */*"
        headers["Sec-Fetch-Dest"] = "empty"
        headers["Sec-Fetch-Mode"] = "cors"
        headers["Sec-Fetch-Site"] = "same-origin"
    else:
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        headers["Sec-Fetch-Dest"] = "document"
        headers["Sec-Fetch-Mode"] = "navigate"
        headers["Sec-Fetch-Site"] = "none"
        headers["Sec-Fetch-User"] = "?1"

    if referer:
        headers["Referer"] = referer

    return headers
