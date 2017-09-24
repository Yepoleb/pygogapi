import json
import re
import logging
import html.parser
import zlib

import requests

from gogapi import urls
from gogapi.base import NotAuthorizedError, logger
from gogapi.product import Product, Series
from gogapi.search import SearchResult

DEBUG_JSON = False
GOGDATA_RE = re.compile(r"gogData\.?(.*?) = (.+);")
CLIENT_VERSION = "1.2.17.9" # Just for their statistics
USER_AGENT = "GOGGalaxyClient/{} pygogapi/0.1".format(CLIENT_VERSION)
REQUEST_RETRIES = 3


PRODUCT_EXPANDABLE = [
    "downloads", "expanded_dlcs", "description", "screenshots", "videos",
    "related_products", "changelog"
]
USER_EXPANDABLE = ["friendStatus", "wishlistStatus", "blockedStatus"]
LOCALE_CODES = ["de-DE", "en-US", "fr-FR", "pt-BR", "ru-RU", "zh-Hans"]
CURRENCY_CODES = [
    "USD", "EUR", "GBP", "AUD", "RUB", "PLN", "CAD", "CHF", "NOK", "SEK", "DKK"
]





def find_scripts(site):
    parser = ScriptParser()
    parser.feed(site)
    return parser.scripts

class ScriptParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.last_tag = None
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        self.last_tag = tag

    def handle_data(self, data):
        if self.last_tag == "script":
            self.scripts.append(data)



class GogApi:
    def __init__(self, token=None):
        self.token = token
        self.locale = (None, None, None) # TODO: replace tuple

    # Helpers

    def request(self, method, url, authorized=True, allow_redirects=False,
                **kwargs):
        # Set headers
        # Prevent getting blocked by default
        headers = {"User-Agent": USER_AGENT}
        # Add a token to the request if it exists
        if self.token is not None:
            if self.token.expired():
                self.token.refresh()
            headers["Authorization"] = "Bearer " + self.token.access_token
        elif authorized:
            raise NotAuthorizedError()

        headers.update(kwargs.pop("headers", {}))

        # Set cookies
        cookies = {}
        if all(self.locale):
            cookies["gog_lc"] = "_".join(self.locale)
        cookies.update(kwargs.pop("cookies", {}))

        # Log request
        if "params" in kwargs:
            full_url = url + "?" + "&".join(
                str(key) + "=" + str(value)
                for key, value in kwargs["params"].items())
            logger.debug("%s %s", method, full_url)
        else:
            logger.debug("%s %s", method, url)

        # Retries
        retries = REQUEST_RETRIES
        while retries > 0:
            resp = requests.request(
                method, url, headers=headers, cookies=cookies, **kwargs)
            if resp.status_code < 400:
                return resp
            elif 400 <= resp.status_code < 500:
                break

        resp.raise_for_status()

    def get(self, *args, **kwargs):
        return self.request("GET", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request("POST", *args, **kwargs)

    def request_json(self, *args, compressed=False, **kwargs):
        resp = self.request(*args, **kwargs)
        if not compressed:
            if DEBUG_JSON:
                logger.debug(resp.text)
            return resp.json()
        else:
            json_comp = resp.content
            json_text = zlib.decompress(json_comp, 15).decode("utf-8")
            if DEBUG_JSON:
                logger.debug(json_text)
            return json.loads(json_text)

    def get_json(self, *args, **kwargs):
        return self.request_json("GET", *args, **kwargs)

    def get_gogdata(self, url, *args, **kwargs):
        resp = self.get(url, *args, **kwargs)
        gogdata = {}
        for script in find_scripts(resp.text):
            matches = GOGDATA_RE.finditer(resp.text)

            for match in matches:
                subkey = match.group(1)
                value = match.group(2)
                value_parsed = json.loads(value)
                if subkey:
                    data = {subkey: value_parsed}
                else:
                    data = value_parsed
                gogdata.update(data)
        return gogdata

    def set_locale(self, country, currency, locale):
        """
        country: ISO 3166 Alpha-2
        currency: ISO 4217
        locale: ISO 639 + ISO 3166 like language[_territory]
        """
        if len(country) != 2:
            return AttributeError("Invalid country code {}".format(country))
        elif currency not in CURRENCY_CODES:
            return AttributeError("Invalid currency code {}".format(locale))
        elif locale not in LOCALE_CODES:
            return AttributeError("Invalid locale code {}".format(locale))
        else:
            self.locale = (country, currency, locale)

    # Web APIs

    def web_game_gogdata(self, slug):
        return self.get_gogdata(urls.web("game", slug), authorized=False)

    def web_games_gogdata(self):
        return self.get_gogdata(urls.web("account.games"))

    def web_movies_gogdata(self):
        return self.get_gogdata(urls.web("account.movies"))

    def web_wishlist_gogdata(self):
        return self.get_gogdata(urls.web("account.wishlist"))

    def web_friends_gogdata(self):
        return self.get_gogdata(urls.web("account.friends"))

    def web_chat_gogdata(self):
        return self.get_gogdata(urls.web("account.chat"))

    def web_wallet_gogdata(self):
        return self.get_gogdata(urls.web("wallet"))

    def web_orders_gogdata(self):
        return self.get_gogdata(urls.web("settings.orders"))

    def web_account_gamedetails(self, game_id):
        return self.get_json(urls.web("account.gamedetails", game_id))

    def web_account_search(self, **query):
        """
        Allowed query keys:
        category: Genre
        feature: Feature
        hiddenFlag: Show hidden games
        language: Language
        mediaType: Game or movie
        page: Page number
        search: Search string
        sortBy: Sort order
        system: OS
        tags: Tags
        totalPages: Total Pages
        """
        return self.get_json(urls.web("account.get_filtered"), params=query)

    def web_search(self, **query):
        """
        Allowed query keys:
        category: Genre
        devpub: Developer or Published
        feature: Features
        language: Language
        mediaType: Game or movie
        page: Page number
        price: Price range
        release: Release timeframe
        search: Search string
        sort: Sort order
        system: OS
        limit: Max results
        """
        return self.get_json(
            urls.web("search.filtering"), params=query, authorized=False)


    def web_user_data(self):
        return self.get_json(urls.web("user.data"))

    def web_user_games(self):
        return self.get_json(urls.web("user.games"))

    def web_user_wishlist(self):
        return self.get_json(urls.web("user.wishlist"))

    def web_user_wishlist_add(self, game_id):
        """Returns new wishlist"""
        return self.get_json(urls.web("user.wishlist.add", game_id))

    def web_user_wishlist_remove(self, game_id):
        """Returns new wishlist"""
        return self.get_json(urls.web("user.wishlist.remove", game_id))

    def web_user_ratings(self):
        return self.get_json(urls.web("user.ratings"))

    def web_user_review_votes(self):
        return self.get_json(urls.web("user.review_votes"))

    def web_user_change_currency(self, currency):
        return self.get_json(urls.web("user.change_currency", currency))

    def web_user_change_language(self, lang):
        return self.get_json(urls.web("user.change_language", lang))

    def web_user_set_redirect_url(self, url):
        """Set redirect url after login. Only know valid url: checkout"""
        return self.get(urls.web("user.set_redirect_url", params={"url": url}))

    def web_user_review_guidelines(self):
        return self.get_json(urls.web("user.review_guidelines"))

    def web_user_public_info(self, user_id, expand=None):
        if not expand:
            params = None
        elif expand == True:
            params = {"expand": ",".join(USER_EXPANDABLE)}
        else:
            params = {"expand": ",".join(expand)}
        return self.get_json(
            urls.web("user.public.info", user_id, params=params))

    def web_user_public_block(self, user_id):
        return self.get_json(urls.web("user.public.block", user_id))

    def web_user_public_unblock(self, user_id):
        return self.get_json(urls.web("user.public.unblock", user_id))


    def web_friends_remove(self, user_id):
        return self.get_json(urls.web("friends.remove", user_id))

    def web_friends_invite(self, user_id):
        return self.get_json(urls.web("friends.invite", user_id))

    def web_friends_accept(self, user_id):
        return self.get_json(urls.web("friends.accept", user_id))

    def web_friends_decline(self, user_id):
        return self.get_json(urls.web("friends.decline", user_id))


    def web_cart_get(self):
        return self.get_json(urls.web("cart.get"))

    def web_cart_add(self, game_id):
        return self.get_json(urls.web("cart.add", game_id))

    def web_cart_add_series(self, series_id):
        return self.get_json(urls.web("cart.add_series", series_id))

    def web_cart_remove(self, game_id):
        return self.get_json(urls.web("cart.remove", game_id))


    def web_reviews_search(self, game_id):
        return self.get_json(urls.web("reviews.search", game_id))

    def web_reviews_vote(self, game_id):
        return self.get_json(urls.web("reviews.vote", game_id))

    def web_reviews_report(self, game_id):
        return self.get_json(urls.web("reviews.report", game_id))

    def web_reviews_rate(self, game_id):
        return self.get_json(urls.web("reviews.rate", game_id))

    def web_reviews_add(self, game_id):
        return self.get_json(urls.web("reviews.add", game_id))


    def web_order_change_currency(self, order_id, currency):
        return self.get_json(
            urls.web("order.change_currency", order_id, currency))

    def web_order_add(self, order_id, game_id):
        return self.get_json(urls.web("order.add", order_id, game_id))

    def web_order_remove(self, order_id, game_id):
        return self.get_json(urls.web("order.remove", order_id, game_id))

    def web_order_enable_store_credit(self, order_id):
        return self.get_json(urls.web("order.enable_store_credit", order_id))

    def web_order_disable_store_credit(self, order_id):
        return self.get_json(urls.web("order.disable_store_credit", order_id))

    def web_order_set_as_gift(self, order_id):
        return self.get_json(urls.web("order.set_as_gift", order_id))

    def web_order_set_as_not_gift(self, order_id):
        return self.get_json(urls.web("order.set_as_non_gift", order_id))

    def web_order_process_order(self, order_id):
        return self.get_json(urls.web("order.process_order", order_id))

    def web_order_payment_status(self, order_id):
        return self.get_json(urls.web("order.payment_status", order_id))

    def web_order_check_status(self, order_id):
        return self.get_json(urls.web("order.check_status", order_id))


    def web_checkout(self, order_id=None):
        if order_id is None:
            return self.get_json(urls.web("checkout"))
        else:
            return self.get_json(urls.web("checkout_id", order_id))

    def web_checkout_manual(self, order_id):
        return self.get_json(urls.web("checkout_manual", order_id))

    # Galaxy APIs

    def galaxy_file(self, game_id, dl_url):
        dl_url = dl_url.lstrip("/")
        return self.get_json(urls.galaxy("file", game_id, dl_url))

    def galaxy_user(self, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(urls.galaxy("user", user_id))

    def galaxy_friends(self, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(urls.galaxy("friends", user_id))

    def galaxy_invitations(self, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(urls.galaxy("invitations", user_id))

    def galaxy_status(self, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        reqdata = {"version": CLIENT_VERSION}
        self.post(urls.galaxy("status", user_id), data=reqdata)

    def galaxy_statuses(self, user_ids):
        user_ids_str = ",".join(user_ids)
        params = {"user_id": user_ids_str}
        #self.request("OPTIONS", urls.galaxy("statuses"), params=params)
        return self.get_json(urls.galaxy("statuses"), params=params)

    def galaxy_achievements(self, game_id, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(urls.galaxy("achievements", game_id, user_id))

    def galaxy_sessions(self, game_id, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(urls.galaxy("sessions", game_id, user_id))

    def galaxy_friends_achievements(self, game_id, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(
            urls.galaxy("friends.achievements", game_id, user_id))

    def galaxy_friends_sessions(self, game_id, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(urls.galaxy("friends.sessions", game_id, user_id))

    def galaxy_product(self, game_id, expand=None):
        if not expand:
            params = {}
        elif expand is True:
            params = {"expand": ",".join(PRODUCT_EXPANDABLE)}
        else:
            params = {"expand": ",".join(expand)}

        if self.locale[2]:
            params["locale"] = self.locale[2]

        return self.get_json(
                urls.galaxy("product", game_id), params=params,
                authorized=False)

    def galaxy_products(self, game_ids, expand=None):
        if not expand:
            params = {}
        elif expand is True:
            params = {"expand": ",".join(PRODUCT_EXPANDABLE)}
        else:
            params = {"expand": ",".join(expand)}

        if self.locale[2]:
            params["locale"] = self.locale[2]

        ids_string = ",".join(str(game_id) for game_id in game_ids)
        params["ids"] = ids_string
        return self.get_json(
            urls.galaxy("products"), params=params, authorized=False)

    def galaxy_builds(self, game_id, system):
        return self.get_json(
            urls.galaxy("cs.builds", game_id, system), authorized=False)

    def galaxy_cs_meta(self, meta_id):
        return self.get_json(
            urls.galaxy("cs.meta", meta_id[0:2], meta_id[2:4], meta_id),
            compressed=True,
            authorized=False)

    def galaxy_client_config():
        return self.get_json(urls.galaxy("client-config"), authorized=False)

    def product(self, product_id):
        return Product(self, product_id)

    def search(self, **query):
        search_data = self.web_search(**query)
        return SearchResult(self, query, search_data)
