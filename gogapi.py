import http.cookiejar
import json
import re
import requests
import urllib.parse
import http.server
import webbrowser
from datetime import datetime, timezone, timedelta
import os.path

PARSE_JSON = True

CLIENT_ID = "46899977096215655"
CLIENT_SECRET = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"
CLIENT_VERSION = "1.1.24.16" # Just for their statistics

PAGE_SUCCESS = """\
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login successful</title>
  </head>
  <body>
    <h1>Login successful!</h1>
    <p>
      You can close this tab now
    </p>
  </body>
</html>
"""

PAGE_ERROR = """\
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login failed</title>
  </head>
  <body>
    <h1>Login failed</h1>
    <p>
      Something went wrong and the login code is missing from the url.
    </p>
  </body>
</html>
"""

#GOGDATA_RE = re.compile(r"var gogData = (\{.+?\});")
GOGDATA_RE = re.compile(r"gogData\.?(.*?) = (.+);")

web_config = {
    "search.filtering": "/games/ajax/filtered",

    "user.data": "/userData.json",
    "user.games": "/user/data/games",
    "user.wishlist": "/user/wishlist.json",
    "user.wishlist.add": "/user/wishlist/add/{}",
    "user.wishlist.remove": "/user/wishlist/remove/{}",
    "user.ratings": "/user/games_rating.json",
    "user.review_votes": "/user/review_votes.json",
    "user.change_currency": "/user/changeCurrency/{}",
    "user.change_language": "/user/changeLanguage/{}",
    "user.set_redirect_url": "/user/set-redirect-url",
    "user.review_guidelines": "/user/reviewTipsStatus.json",
    "user.public.info": "/users/info/{}",
    "user.public.block": "/users/{}/block",
    "user.public.unblock": "/users/{}/unblock",

    "friends.remove": "/friends/remove/{}",
    "friends.invite": "/friends/invite/{}",
    "friends.accept": "/friends/invites/{}/accept",
    "friends.decline": "/friends/invites/{}/decline",

    "cart.get": "/cart",
    "cart.add": "/cart/add/{}",
    "cart.add_series": "/cart/add/series/{}",
    "cart.remove": "/cart/remove/{}",

    "reviews.search": "/reviews/product/{}.json",
    "reviews.vote": "/reviews/vote/review/{}.json",
    "reviews.report": "/reviews/report/review/{}.json",
    "reviews.rate": "/reviews/rate/product/{}.json",
    "reviews.add": "/reviews/add/product/{}.json",

    "order.change_currency": "/checkout/order/{}/changeCurrency/{}",
    "order.add": "/checkout/order/{}/add/{}",
    "order.remove": "/checkout/order/{}/remove/{}",
    "order.enable_store_credit": "/checkout/order/{}/enableStoreCredit",
    "order.disable_store_credit": "/checkout/order/{}/disableStoreCredit",
    "order.set_as_gift": "/checkout/order/{}/setAsGift",
    "order.set_as_not_gift": "/checkout/order/{}/setAsNotGift",
    "order.process_order": "/payment/process/{}",
    "order.payment_status": "/payment/ping/{}",
    "order.check_status": "/order/checkStatus/{}",

    "checkout": "/checkout",
    "checkout_id": "/checkout/{}",
    "checkout_manual": "/checkout/manual/{}",

    # Manual

    "account.games": "/account",
    "account.movies": "/account/movies",
    "account.wishlist": "/account/wishlist",
    "account.friends": "/account/friends",
    "account.chat": "/account/chat",
    "account.gamedetails": "/account/gameDetails/{}.json",
    "account.get_filtered": "/account/getFilteredProducts",

    "wallet": "/wallet",

    "settings.orders": "/orders"
}

galaxy_config = {
    "file": "api:/products/{}/{}",
    "user": "users:/users/{}",
    "friends": "chat:/users/{}/friends",
    "invitations": "chat:/users/{}/invitations",
    "status": "presence:/users/{}/status",
    "statuses": "presence:/statuses",
    "achievements": "gameplay:/clients/{}/users/{}/achievements",
    "sessions": "gameplay:/clients/{}/users/{}/sessions",
    "friends.achievements":
        "gameplay:/clients/{}/users/{}/friends_achievements_unlock_progresses",
    "friends.sessions": "gameplay:/clients/{}/users/{}/friends_sessions",
    "product": "api:/products/{}",
    "auth": "auth:/auth?client_id={client_id}&redirect_uri={redir_uri}&response_type=code&layout=client2",
    "token": "auth:/token",
    "client-config": "cfg:/desktop-galaxy-client/config.json",
    "cs.builds": "cont:/products/{}/os/{}/builds?generation=2"#,
    #"cs.mainfests": "cdn:/content-system/v1/manifests/{}
}

gog_servers = {
    "gog": "https://www.gog.com",
    "embed": "https://embed.gog.com",
    "api": "https://api.gog.com",
    "users": "https://users.gog.com",
    "chat": "https://chat.gog.com",
    "presence": "https://presence.gog.com",
    "gameplay": "https://gameplay.gog.com",
    "cfg": "https://cfg.gog.com",
    "auth": "https://auth.gog.com",
    "cont": "https://content-system.gog.com",
    "cdn": "https://cdn.gog.com"
}

PRODUCT_EXPANDABLE = [
    "downloads", "expanded_dlcs", "description", "screenshots", "videos",
    "related_products", "changelog"]
USER_EXPANDABLE = ["friendStatus", "wishlistStatus", "blockedStatus"]

def web_url(url_id, *args, **kwargs):
    host_url = gog_servers["embed"]
    api_path = web_config[url_id]
    url = urllib.parse.urljoin(host_url, api_path)
    url_args = url.format(*args, **kwargs)
    return url_args

def galaxy_url(url_id, *args, **kwargs):
    url_config = galaxy_config[url_id]
    host_id, api_path = url_config.split(':', 1)
    host_url = gog_servers[host_id]
    url = urllib.parse.urljoin(host_url, api_path)
    url_args = url.format(*args, **kwargs)
    return url_args

def galaxy_client_config():
    resp = requests.get(galaxy_url("client-config"))
    return resp.json()

class ApiError(Exception):
    def __init__(self, error, description):
        self.error = error
        self.description = description

class GogApi:
    def __init__(self, token):
        self.token = token

    # Helpers

    def request(self, *args, **kwargs):
        if self.token.expired():
            self.token.refresh()
        headers = {"Authorization": "Bearer " + token.access_token}
        headers.update(kwargs.pop("headers", {}))
        return requests.request(*args, headers=headers, **kwargs)

    def get(self, *args, **kwargs):
        return self.request(self, "GET", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request(self, "POST", *args, **kwargs)

    def request_json(self, *args, **kwargs):
        resp = self.request(*args, **kwargs)
        if PARSE_JSON:
            return json.loads(resp.text)
        else:
            return resp.text

    def get_json(self, *args, **kwargs):
        return self.request_json("GET", *args, **kwargs)

    def get_gogdata(self, url, *args, **kwargs):
        # TODO: Limit to <script> tags to prevent injection from user content
        resp = self.get(url, *args, **kwargs)
        matches = GOGDATA_RE.finditer(resp.text)
        gogdata = {}
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

    # Web APIs

    def web_games_gogdata(self):
        return self.get_gogdata(web_url("account.games"))

    def web_movies_gogdata(self):
        return self.get_gogdata(web_url("account.movies"))

    def web_wishlist_gogdata(self):
        return self.get_gogdata(web_url("account.wishlist"))

    def web_friends_gogdata(self):
        return self.get_gogdata(web_url("account.friends"))

    def web_chat_gogdata(self):
        return self.get_gogdata(web_url("account.chat"))

    def web_wallet_gogdata(self):
        return self.get_gogdata(web_url("wallet"))

    def web_orders_gogdata(self):
        return self.get_gogdata(web_url("settings.orders"))

    def web_account_gamedetails(self, game_id):
        return self.get_json(web_url("account.gamedetails", game_id))

    def web_account_search(self):
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
        return self.get_json(web_url("account.get_filtered"), params=query)

    def web_search(self, query):
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
        return self.get_json(web_url("search.filtering"), params=query)


    def web_user_data(self):
        return self.get_json(web_url("user.data"))

    def web_user_games(self):
        return self.get_json(web_url("user.games"))

    def web_user_wishlist(self):
        return self.get_json(web_url("user.wishlist"))

    def web_user_wishlist_add(self, game_id):
        """Returns new wishlist"""
        return self.get_json(web_url("user.wishlist.add", game_id))

    def web_user_wishlist_remove(self, game_id):
        """Returns new wishlist"""
        return self.get_json(web_url("user.wishlist.remove", game_id))

    def web_user_ratings(self):
        return self.get_json(web_url("user.ratings"))

    def web_user_review_votes(self):
        return self.get_json(web_url("user.review_votes"))

    def web_user_change_currency(self, currency):
        return self.get_json(web_url("user.change_currency", currency))

    def web_user_change_language(self, lang):
        return self.get_json(web_url("user.change_language", lang))

    def web_user_set_redirect_url(self, url):
        """Set redirect url after login. Only know valid url: checkout"""
        return self.get(web_url("user.set_redirect_url", params={"url": url}))

    def web_user_review_guidelines(self):
        return self.get_json(web_url("user.review_guidelines"))

    def web_user_public_info(self, user_id, expand=None):
        if not expand:
            params = None
        elif expand == True:
            params = {"expand": ",".join(USER_EXPANDABLE)}
        else:
            params = {"expand": ",".join(expand)}
        return self.get_json(
            web_url("user.public.info", user_id, params=params))

    def web_user_public_block(self, user_id):
        return self.get_json(web_url("user.public.block", user_id))

    def web_user_public_unblock(self, user_id):
        return self.get_json(web_url("user.public.unblock", user_id))


    def web_friends_remove(self, user_id):
        return self.get_json(web_url("friends.remove", user_id))

    def web_friends_invite(self, user_id):
        return self.get_json(web_url("friends.invite", user_id))

    def web_friends_accept(self, user_id):
        return self.get_json(web_url("friends.accept", user_id))

    def web_friends_decline(self, user_id):
        return self.get_json(web_url("friends.decline", user_id))


    def web_cart_get(self):
        return self.get_json(web_url("cart.get"))

    def web_cart_add(self, game_id):
        return self.get_json(web_url("cart.add", game_id))

    def web_cart_add_series(self, series_id):
        return self.get_json(web_url("cart.add_series", series_id))

    def web_cart_remove(self, game_id):
        return self.get_json(web_url("cart.remove", game_id))


    def web_reviews_search(self, game_id):
        return self.get_json(web_url("reviews.search", game_id))

    def web_reviews_vote(self, game_id):
        return self.get_json(web_url("reviews.vote", game_id))

    def web_reviews_report(self, game_id):
        return self.get_json(web_url("reviews.report", game_id))

    def web_reviews_rate(self, game_id):
        return self.get_json(web_url("reviews.rate", game_id))

    def web_reviews_add(self, game_id):
        return self.get_json(web_url("reviews.add", game_id))


    def web_order_change_currency(self, order_id, currency):
        return self.get_json(
            web_url("order.change_currency", order_id, currency))

    def web_order_add(self, order_id, game_id):
        return self.get_json(web_url("order.add", order_id, game_id))

    def web_order_remove(self, order_id, game_id):
        return self.get_json(web_url("order.remove", order_id, game_id))

    def web_order_enable_store_credit(self, order_id):
        return self.get_json(web_url("order.enable_store_credit", order_id))

    def web_order_disable_store_credit(self, order_id):
        return self.get_json(web_url("order.disable_store_credit", order_id))

    def web_order_set_as_gift(self, order_id):
        return self.get_json(web_url("order.set_as_gift", order_id))

    def web_order_set_as_not_gift(self, order_id):
        return self.get_json(web_url("order.set_as_non_gift", order_id))

    def web_order_process_order(self, order_id):
        return self.get_json(web_url("order.process_order", order_id))

    def web_order_payment_status(self, order_id):
        return self.get_json(web_url("order.payment_status", order_id))

    def web_order_check_status(self, order_id):
        return self.get_json(web_url("order.check_status", order_id))


    def web_checkout(self, order_id=None):
        if order_id is None:
            return self.get_json(web_url("checkout"))
        else:
            return self.get_json(web_url("checkout_id", order_id))

    def web_checkout_manual(self, order_id):
        return self.get_json(web_url("checkout_manual", order_id))

    # Galaxy APIs

    def galaxy_file(self, game_id, dl_url):
        dl_url = dl_url.lstrip("/")
        return self.get_json(galaxy_url("file", game_id, dl_url))

    def galaxy_user(self, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(galaxy_url("user", user_id))

    def galaxy_friends(self, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(galaxy_url("friends", user_id))

    def galaxy_invitations(self, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(galaxy_url("invitations", user_id))

    def galaxy_status(self, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        reqdata = {"version": CLIENT_VERSION}
        self.post(galaxy_url("status", user_id), data=reqdata)

    def galaxy_statuses(self, user_ids):
        user_ids_str = ",".join(user_ids)
        params = {"user_id": user_ids_str}
        #self.request("OPTIONS", galaxy_url("statuses"), params=params)
        return self.get_json(galaxy_url("statuses"), params=params)

    def galaxy_achievements(self, game_id, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(galaxy_url("achievements", game_id, user_id))

    def galaxy_sessions(self, game_id, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(galaxy_url("sessions", game_id, user_id))

    def galaxy_friends_achievements(self, game_id, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(
            galaxy_url("friends.achievements", game_id, user_id))

    def galaxy_friends_sessions(self, game_id, user_id=None):
        if user_id is None:
            user_id = self.token.user_id
        return self.get_json(galaxy_url("friends.sessions", game_id, user_id))

    def galaxy_product(self, game_id, expand=None):
        if not expand:
            params = None
        elif expand == True:
            params = {"expand": ",".join(PRODUCT_EXPANDABLE)}
        else:
            params = {"expand": ",".join(expand)}
        return self.get_json(galaxy_url("product", game_id, params=params))



class LoginRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path_urlparse = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(path_urlparse.query)
        if "code" not in query:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(PAGE_ERROR.encode("utf8"))
            self.server.login_code = None
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(PAGE_SUCCESS.encode("utf8"))
            self.server.login_code = query["code"][0]

class Token:
    def set_data(self, token_data):
        if "error" in token_data:
            raise ApiError(token_data["error"], token_data["error_description"])

        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.expires_in = timedelta(seconds=token_data["expires_in"])
        self.scope = token_data["scope"]
        self.session_id = token_data["session_id"]
        self.token_type = token_data["token_type"]
        self.user_id = token_data["user_id"]
        if "created" in token_data:
            self.created = datetime.fromtimestamp(
                token_data["created"], tz=timezone.utc)
        else:
            self.created = datetime.now(tz=timezone.utc)

    def get_data(self):
        token_data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": int(self.expires_in.total_seconds()),
            "scope": self.scope,
            "session_id": self.session_id,
            "token_type": self.token_type,
            "user_id": self.user_id,
            "created": int(self.created.timestamp())
        }
        return token_data

    def __repr__(self):
        return str(self.__dict__)

    def load(self, filename):
        with open(filename, "r") as f:
            self.set_data(json.load(f))

    def save(self, filename):
        with open(filename, "w") as f:
            json.dump(self.get_data(), f, indent=2, sort_keys=True)

    def from_file(filename):
        token = Token()
        token.load(filename)
        return token

    def from_login(server_ip="127.0.0.1", browser_callback=None):
        httpd = http.server.HTTPServer((server_ip, 0), LoginRequestHandler)

        redirect_url = "http://{}:{}/token".format(*httpd.server_address)
        redirect_url_quoted = urllib.parse.quote(redirect_url)
        auth_url = galaxy_url(
            "auth", client_id=CLIENT_ID, redir_uri=redirect_url_quoted)
        if browser_callback is None:
            webbrowser.open_new_tab(auth_url)
            print("Your web browser has been opened to allow you to log in.")
            print("If that didn't work, please manually open", auth_url)
        else:
            browser_callback(auth_url)

        httpd.handle_request()
        httpd.server_close()
        if httpd.login_code is None:
            raise Exception("Authorization failed")

        token_query = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": httpd.login_code,
            "redirect_uri": redirect_url # Needed for origin verification
        }
        token_resp = requests.get(galaxy_url("token"), params=token_query)
        token = Token()
        token.set_data(token_resp.json())
        return token

    def refresh(self):
        token_query = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        token_resp = requests.get(galaxy_url("token"), params=token_query)
        self.set_data(token_resp.json())

    def expired(self, margin=timedelta(seconds=60)):
        expires_at = self.created + self.expires_in
        return (datetime.now(timezone.utc) - expires_at) > margin



if __name__ == "__main__":
    try:
        token = Token.from_file("token.json")
        token.refresh()
    except (ApiError, FileNotFoundError) as e:
        token = Token.from_login()
    token.save("token.json")

    api = GogApi(token)

    from pprint import pprint
    pprint(api.web_user_data())
