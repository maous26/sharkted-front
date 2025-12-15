"""
Service Vinted - Matching et récupération des stats de marché
Version améliorée avec authentification automatique robuste + Proxy Webshare
"""

import asyncio
import re
import statistics
import random
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import httpx
from loguru import logger

from config import settings


class VintedService:
    """Service pour interagir avec Vinted et calculer les stats de marché"""

    # URLs Vinted
    BASE_URL = "https://www.vinted.fr"
    SEARCH_URL = f"{BASE_URL}/api/v2/catalog/items"

    # User agents réalistes (navigateurs récents)
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    def __init__(self):
        self._cookies: Dict[str, str] = {}
        self._session_expires: Optional[datetime] = None
        self._user_agent = random.choice(self.USER_AGENTS)
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum 1 seconde entre les requêtes
        self._proxies: List[str] = []
        self._proxies_loaded_at: Optional[datetime] = None
        self._current_proxy_index = 0

    async def _load_proxies(self, force: bool = False) -> bool:
        """Charge la liste des proxies depuis Webshare"""
        # Recharger si > 1 heure ou force
        if not force and self._proxies and self._proxies_loaded_at:
            if datetime.now() - self._proxies_loaded_at < timedelta(hours=1):
                return True

        if not settings.USE_ROTATING_PROXY or not settings.WEBSHARE_PROXY_URL:
            logger.debug("Proxies désactivés ou URL non configurée")
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(settings.WEBSHARE_PROXY_URL)
                if response.status_code == 200:
                    # Format: ip:port:username:password
                    lines = response.text.strip().split('\n')
                    self._proxies = []
                    for line in lines:
                        parts = line.strip().split(':')
                        if len(parts) >= 4:
                            ip, port, username, password = parts[0], parts[1], parts[2], parts[3]
                            proxy_url = f"http://{username}:{password}@{ip}:{port}"
                            self._proxies.append(proxy_url)
                        elif len(parts) == 2:
                            # Format simple ip:port
                            self._proxies.append(f"http://{parts[0]}:{parts[1]}")

                    self._proxies_loaded_at = datetime.now()
                    logger.info(f"✅ {len(self._proxies)} proxies Webshare chargés")
                    return len(self._proxies) > 0
                else:
                    logger.warning(f"Échec chargement proxies: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Erreur chargement proxies: {e}")
            return False

    def _get_proxy(self) -> Optional[str]:
        """Retourne le prochain proxy en rotation"""
        if not self._proxies or not settings.USE_ROTATING_PROXY:
            return None

        proxy = self._proxies[self._current_proxy_index % len(self._proxies)]
        self._current_proxy_index += 1
        return proxy

    def _get_client_kwargs(self) -> Dict[str, Any]:
        """Retourne les kwargs pour httpx.AsyncClient avec proxy si disponible"""
        kwargs: Dict[str, Any] = {
            "timeout": 30.0,
            "follow_redirects": True,
            "http2": True
        }

        proxy = self._get_proxy()
        if proxy:
            kwargs["proxy"] = proxy
            logger.debug(f"Utilisation proxy: {proxy.split('@')[1] if '@' in proxy else proxy}")

        return kwargs

    def _get_headers(self, with_cookies: bool = True, for_api: bool = False) -> Dict[str, str]:
        """Génère les headers réalistes pour les requêtes"""
        headers = {
            "User-Agent": self._user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
        }

        if for_api:
            headers["Sec-Fetch-Dest"] = "empty"
            headers["Sec-Fetch-Mode"] = "cors"
            headers["Sec-Fetch-Site"] = "same-origin"
            headers["Referer"] = f"{self.BASE_URL}/catalog"
            headers["Origin"] = self.BASE_URL
        else:
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            headers["Sec-Fetch-Dest"] = "document"
            headers["Sec-Fetch-Mode"] = "navigate"
            headers["Sec-Fetch-Site"] = "none"
            headers["Sec-Fetch-User"] = "?1"

        if with_cookies and self._cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in self._cookies.items()])
            headers["Cookie"] = cookie_str

        return headers

    def _is_session_valid(self) -> bool:
        """Vérifie si la session est encore valide"""
        if not self._cookies or not self._session_expires:
            return False
        return datetime.now() < self._session_expires

    async def _rate_limit(self):
        """Applique un rate limiting pour éviter le blocage"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - elapsed + random.uniform(0.1, 0.5))
        self._last_request_time = time.time()

    async def _init_session(self, force: bool = False) -> bool:
        """
        Initialise une session Vinted valide.

        La stratégie:
        1. Charger les proxies si activés
        2. Visiter la page d'accueil pour obtenir les cookies initiaux
        3. Faire une requête vers le catalog pour valider la session
        4. Stocker tous les cookies pour les requêtes suivantes
        """
        if not force and self._is_session_valid():
            return True

        logger.info("Initialisation d'une nouvelle session Vinted...")

        # Charger les proxies si activés
        await self._load_proxies()

        # Changer de user agent pour chaque nouvelle session
        self._user_agent = random.choice(self.USER_AGENTS)
        self._cookies = {}

        try:
            async with httpx.AsyncClient(**self._get_client_kwargs()) as client:
                # Étape 1: Visiter la page d'accueil
                await self._rate_limit()
                response = await client.get(
                    self.BASE_URL,
                    headers=self._get_headers(with_cookies=False)
                )

                if response.status_code != 200:
                    logger.warning(f"Échec accès page d'accueil Vinted: {response.status_code}")
                    return False

                # Collecter les cookies
                for cookie in response.cookies.jar:
                    if cookie.value is not None:
                        self._cookies[cookie.name] = cookie.value

                logger.debug(f"Cookies initiaux: {list(self._cookies.keys())}")

                # Étape 2: Visiter le catalog pour simuler une navigation
                await self._rate_limit()
                catalog_response = await client.get(
                    f"{self.BASE_URL}/catalog",
                    headers=self._get_headers(with_cookies=True)
                )

                # Collecter les cookies supplémentaires
                for cookie in catalog_response.cookies.jar:
                    if cookie.value is not None:
                        self._cookies[cookie.name] = cookie.value

                # Étape 3: Faire une recherche simple pour activer la session API
                await self._rate_limit()
                test_params = {
                    "search_text": "nike",
                    "per_page": 1,
                    "order": "relevance",
                }

                api_response = await client.get(
                    self.SEARCH_URL,
                    params=test_params,
                    headers=self._get_headers(with_cookies=True, for_api=True)
                )

                # Collecter tous les cookies
                for cookie in api_response.cookies.jar:
                    if cookie.value is not None:
                        self._cookies[cookie.name] = cookie.value

                if api_response.status_code == 200:
                    # Session valide pour 30 minutes
                    self._session_expires = datetime.now() + timedelta(minutes=30)
                    logger.info(f"Session Vinted initialisée avec succès ({len(self._cookies)} cookies)")
                    return True
                else:
                    logger.warning(f"Échec validation session API: {api_response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Erreur initialisation session Vinted: {e}")
            return False

    def _build_search_query(
        self,
        product_name: str,
        brand: Optional[str] = None,
        category: Optional[str] = None
    ) -> str:
        """Construit la query de recherche optimisée"""

        # Nettoyer le nom du produit
        clean_name = re.sub(r'[^\w\s-]', ' ', product_name)

        # Extraire les mots-clés importants
        keywords = []

        # Ajouter la marque si présente (et pas déjà dans le nom)
        if brand and brand.lower() not in clean_name.lower():
            keywords.append(brand.lower())

        # Stop words à ignorer
        stop_words = {
            'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'pour',
            'homme', 'femme', 'men', 'women', 'mens', 'womens', 'size',
            'taille', 'new', 'neuf', 'with', 'avec', 'the', 'and', 'or',
            'chaussures', 'shoes', 'sneakers', 'basket', 'baskets'
        }

        # Extraire les mots significatifs
        words = clean_name.lower().split()
        for word in words:
            word = word.strip('-')
            if len(word) > 2 and word not in stop_words and word not in keywords:
                keywords.append(word)

        # Garder les 4-5 mots-clés les plus importants
        keywords = keywords[:5]

        return " ".join(keywords)

    async def search_products(
        self,
        query: str,
        limit: int = 50,
        price_from: Optional[float] = None,
        price_to: Optional[float] = None,
        status: str = "all",
        retry_count: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Recherche des produits sur Vinted avec retry automatique.

        Args:
            query: Termes de recherche
            limit: Nombre max de résultats
            price_from: Prix minimum
            price_to: Prix maximum
            status: "all", "active" (en vente), "sold" (vendu)
            retry_count: Nombre de retry (interne)

        Returns:
            Liste des annonces trouvées
        """

        # Initialiser la session si nécessaire
        if not self._is_session_valid():
            session_ok = await self._init_session()
            if not session_ok:
                logger.warning("Impossible d'initialiser la session Vinted")
                return []

        # Construire les paramètres
        params = {
            "search_text": query,
            "per_page": min(limit, 96),
            "order": "relevance",
            "currency": "EUR",
            "page": 1,
        }

        if price_from:
            params["price_from"] = int(price_from)
        if price_to:
            params["price_to"] = int(price_to)

        # Filtrer par statut (vendu = meilleur indicateur de prix réel)
        if status == "sold":
            params["status[]"] = "sold"

        try:
            await self._rate_limit()

            async with httpx.AsyncClient(**self._get_client_kwargs()) as client:
                response = await client.get(
                    self.SEARCH_URL,
                    params=params,
                    headers=self._get_headers(with_cookies=True, for_api=True)
                )

                # Mettre à jour les cookies
                for cookie in response.cookies.jar:
                    if cookie.value is not None:
                        self._cookies[cookie.name] = cookie.value

                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    logger.debug(f"Vinted: {len(items)} résultats pour '{query}'")
                    return items

                elif response.status_code == 401 and retry_count < 2:
                    # Session expirée, réinitialiser et réessayer
                    logger.info("Session Vinted expirée, réinitialisation...")
                    self._cookies = {}
                    self._session_expires = None
                    await asyncio.sleep(1 + random.uniform(0.5, 1.5))
                    return await self.search_products(query, limit, price_from, price_to, retry_count + 1)

                elif response.status_code == 429:
                    # Rate limited, attendre et réessayer
                    logger.warning("Rate limit Vinted, attente 30s...")
                    await asyncio.sleep(30)
                    if retry_count < 2:
                        return await self.search_products(query, limit, price_from, price_to, retry_count + 1)
                    return []

                else:
                    logger.warning(f"Vinted search error: {response.status_code}")
                    return []

        except httpx.TimeoutException:
            logger.warning("Timeout sur la recherche Vinted")
            if retry_count < 2:
                await asyncio.sleep(2)
                return await self.search_products(query, limit, price_from, price_to, retry_count + 1)
            return []

        except Exception as e:
            logger.error(f"Erreur recherche Vinted: {e}")
            return []

    def _extract_price(self, item: Dict) -> Optional[float]:
        """Extrait le prix d'une annonce"""
        try:
            # Essayer le champ price directement
            price = item.get("price")
            if price:
                if isinstance(price, (int, float)):
                    return float(price)
                if isinstance(price, str):
                    price_match = re.search(r'(\d+[.,]?\d*)', price)
                    if price_match:
                        return float(price_match.group(1).replace(',', '.'))

            # Essayer total_item_price
            total_price = item.get("total_item_price")
            if total_price:
                if isinstance(total_price, dict):
                    amount = total_price.get("amount")
                    if amount:
                        return float(amount)
                elif isinstance(total_price, (int, float)):
                    return float(total_price)

            # Essayer price_numeric
            price_numeric = item.get("price_numeric")
            if price_numeric:
                return float(price_numeric)

            return None
        except Exception:
            return None

    async def get_market_stats(
        self,
        product_name: str,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        expected_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Récupère les statistiques de marché Vinted pour un produit.
        Combine les articles en vente ET les articles vendus pour des prix plus réalistes.

        Args:
            product_name: Nom du produit
            brand: Marque
            category: Catégorie
            expected_price: Prix attendu (pour filtrer les aberrants)

        Returns:
            Dictionnaire avec les stats de marché
        """

        # Construire la query de recherche
        query = self._build_search_query(product_name, brand, category)

        # Définir les limites de prix - prix max = 2x le prix d'achat (occasion)
        # On cherche des prix occasion, pas des prix neufs
        price_to = expected_price * 2 if expected_price else None
        price_from = 5  # Minimum 5€ pour filtrer les annonces invalides

        # Rechercher les articles EN VENTE
        active_items = await self.search_products(
            query=query,
            limit=settings.VINTED_SEARCH_LIMIT // 2,
            price_from=price_from,
            price_to=price_to,
            status="all"
        )

        # Rechercher les articles VENDUS (vrais prix de marché)
        sold_items = await self.search_products(
            query=query,
            limit=settings.VINTED_SEARCH_LIMIT // 2,
            price_from=price_from,
            price_to=price_to,
            status="sold"
        )

        # Combiner les résultats (priorité aux vendus)
        items = sold_items + active_items
        nb_sold = len(sold_items)
        nb_active = len(active_items)

        if not items:
            logger.info(f"Aucun résultat Vinted pour: {query}")
            return {
                "nb_listings": 0,
                "nb_sold": 0,
                "prices": [],
                "query_used": query
            }

        # Extraire les prix
        prices = []
        sample_listings = []

        for item in items:
            price = self._extract_price(item)
            if price and price >= 5:  # Minimum 5€
                prices.append(price)

                # Garder quelques exemples
                if len(sample_listings) < 5:
                    photo = item.get("photo", {}) or {}
                    sample_listings.append({
                        "title": item.get("title", ""),
                        "price": price,
                        "url": f"{self.BASE_URL}/items/{item.get('id', '')}",
                        "photo_url": photo.get("url", "") if isinstance(photo, dict) else "",
                        "size": item.get("size_title", ""),
                        "brand": item.get("brand_title", "")
                    })

        if not prices:
            return {
                "nb_listings": len(items),
                "nb_sold": nb_sold,
                "nb_active": nb_active,
                "prices": [],
                "query_used": query
            }

        # Filtrer les outliers de manière plus agressive
        # 1. D'abord, si on a un expected_price, filtrer les prix trop au-dessus
        if expected_price:
            # Les articles occasion sont généralement entre 50% et 150% du prix neuf
            max_reasonable = expected_price * 1.5
            filtered_prices = [p for p in prices if p <= max_reasonable]
            if len(filtered_prices) < 5:
                # Si trop peu de résultats, on garde tout
                filtered_prices = prices
        else:
            filtered_prices = prices

        # 2. Ensuite, filtrer les outliers (prix > 2x la médiane)
        if len(filtered_prices) >= 5:
            initial_median = statistics.median(filtered_prices)
            filtered_prices = [p for p in filtered_prices if p <= initial_median * 2]

        if len(filtered_prices) < 3:
            filtered_prices = prices

        # Calculer les statistiques
        sorted_prices = sorted(filtered_prices)
        nb_prices = len(filtered_prices)

        stats = {
            "nb_listings": len(items),
            "nb_sold": nb_sold,
            "nb_active": nb_active,
            "prices": filtered_prices,
            "query_used": query,
            "price_min": round(min(filtered_prices), 2),
            "price_max": round(max(filtered_prices), 2),
            "price_avg": round(statistics.mean(filtered_prices), 2),
            "price_median": round(statistics.median(filtered_prices), 2),
            "price_p25": round(sorted_prices[max(0, int(nb_prices * 0.25) - 1)], 2),
            "price_p75": round(sorted_prices[min(nb_prices - 1, int(nb_prices * 0.75))], 2),
            "sample_listings": sample_listings
        }

        # Calculer la dispersion des prix
        if nb_prices >= 2:
            stats["price_std"] = round(statistics.stdev(filtered_prices), 2)
            stats["coefficient_variation"] = round(stats["price_std"] / stats["price_avg"] * 100, 1) if stats["price_avg"] > 0 else 0

        logger.info(f"Vinted stats pour '{query}': {nb_prices} prix ({nb_sold} vendus, {nb_active} en vente), médiane {stats['price_median']}€")

        return stats

    def calculate_margin(
        self,
        buy_price: float,
        vinted_stats: Dict[str, Any],
        use_percentile: str = "p25"
    ) -> Tuple[float, float]:
        """
        Calcule la marge potentielle.

        Args:
            buy_price: Prix d'achat
            vinted_stats: Stats Vinted
            use_percentile: "p25" (conservateur), "median", "p75" (optimiste)

        Returns:
            Tuple (marge en €, marge en %)
        """

        if use_percentile == "p25":
            sell_price = vinted_stats.get("price_p25", 0)
        elif use_percentile == "p75":
            sell_price = vinted_stats.get("price_p75", 0)
        else:
            sell_price = vinted_stats.get("price_median", 0)

        if not sell_price or sell_price <= 0:
            return 0.0, 0.0

        # Frais Vinted: ~5% de commission + ~3% frais de paiement
        vinted_commission = sell_price * 0.05
        payment_fees = sell_price * 0.03

        # Frais de port estimés (à la charge du vendeur si boost)
        shipping_estimate = 4.50

        net_sell_price = sell_price - vinted_commission - payment_fees - shipping_estimate
        margin_euro = net_sell_price - buy_price
        margin_percent = (margin_euro / buy_price * 100) if buy_price > 0 else 0

        return round(margin_euro, 2), round(margin_percent, 1)

    def calculate_liquidity_score(self, vinted_stats: Dict[str, Any]) -> float:
        """
        Calcule un score de liquidité (0-100).

        Facteurs:
        - Nombre d'annonces (demande/offre)
        - Dispersion des prix (marché stable)
        """

        nb_listings = vinted_stats.get("nb_listings", 0)

        if nb_listings == 0:
            return 0.0

        # Score basé sur le nombre d'annonces (max 60 points)
        # 50+ annonces = score max
        if nb_listings >= 50:
            listings_score = 60
        elif nb_listings >= 30:
            listings_score = 50
        elif nb_listings >= 15:
            listings_score = 40
        elif nb_listings >= 5:
            listings_score = 25
        else:
            listings_score = nb_listings * 4

        # Score basé sur la stabilité des prix (max 40 points)
        cv = vinted_stats.get("coefficient_variation", 100)
        if cv <= 15:
            dispersion_score = 40  # Très stable
        elif cv <= 25:
            dispersion_score = 30
        elif cv <= 40:
            dispersion_score = 20
        elif cv <= 60:
            dispersion_score = 10
        else:
            dispersion_score = 0

        total_score = listings_score + dispersion_score

        return round(min(total_score, 100), 1)


# Instance singleton
vinted_service = VintedService()


async def get_vinted_stats_for_deal(
    product_name: str,
    brand: Optional[str],
    sale_price: float,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fonction helper pour obtenir les stats Vinted complètes pour un deal.

    Le sale_price est le prix d'achat en magasin (avec promo).
    On cherche les prix occasion sur Vinted qui devraient être
    inférieurs ou proches du prix magasin original.
    """

    # Récupérer les stats de marché
    # expected_price = prix d'achat, les prix Vinted occasion devraient
    # être autour de ce prix pour que le flip soit rentable
    stats = await vinted_service.get_market_stats(
        product_name=product_name,
        brand=brand,
        category=category,
        expected_price=sale_price
    )

    if stats.get("nb_listings", 0) == 0 or not stats.get("prices"):
        return {
            "nb_listings": 0,
            "margin_euro": 0,
            "margin_percent": 0,
            "liquidity_score": 0,
            "sample_listings": []
        }

    # Calculer la marge avec le prix P25 (conservateur)
    margin_euro, margin_percent = vinted_service.calculate_margin(
        buy_price=sale_price,
        vinted_stats=stats,
        use_percentile="p25"
    )

    # Calculer le score de liquidité
    liquidity_score = vinted_service.calculate_liquidity_score(stats)

    return {
        "nb_listings": stats.get("nb_listings", 0),
        "nb_listings_by_size": {},
        "price_min": stats.get("price_min"),
        "price_max": stats.get("price_max"),
        "price_avg": stats.get("price_avg"),
        "price_median": stats.get("price_median"),
        "price_p25": stats.get("price_p25"),
        "price_p75": stats.get("price_p75"),
        "coefficient_variation": stats.get("coefficient_variation"),
        "margin_euro": margin_euro,
        "margin_percent": margin_percent,
        "liquidity_score": liquidity_score,
        "sample_listings": stats.get("sample_listings", []),
        "query_used": stats.get("query_used", "")
    }
