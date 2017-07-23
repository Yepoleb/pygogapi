import urllib.parse


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
    "cs.builds": "cont:/products/{}/os/{}/builds?generation=2",
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

def web(url_id, *args, **kwargs):
    host_url = gog_servers["embed"]
    api_path = web_config[url_id]
    url = urllib.parse.urljoin(host_url, api_path)
    url_args = url.format(*args, **kwargs)
    return url_args

def galaxy(url_id, *args, **kwargs):
    url_config = galaxy_config[url_id]
    host_id, api_path = url_config.split(':', 1)
    host_url = gog_servers[host_id]
    url = urllib.parse.urljoin(host_url, api_path)
    url_args = url.format(*args, **kwargs)
    return url_args
