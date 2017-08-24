from datetime import datetime
import itertools

import dateutil.parser
from decimal import Decimal

from gogapi.contentsystem import Build
from gogapi.download import Download
from gogapi.normalization import normalize_system

GOGDATA_TYPE = {
    1: "game",
    2: "pack",
    3: "dlc"
}



def parse_systems(system_compat):
    return [
        normalize_system(system)
        for system, supported in system_compat.items() if supported]

def parse_system_reqs(system_reqs):
    if not system_reqs:
        return None
    else:
        return dict(
            (normalize_system(system), reqs)
            for system, reqs in system_reqs.items())

def parse_price(price_data):
    return Price(
        base=Decimal(price_data["baseAmount"]),
        final=Decimal(price_data["finalAmount"]),
        symbol=price_data["symbol"],
        promo_id=price_data.get("promoId", None))

def maybe_timestamp(timestamp):
    if not timestamp:
        return None
    if isinstance(timestamp, int):
        return datetime.fromtimestamp(float(timestamp))
    else:
        return dateutil.parser.parse(timestamp)

def add_products_gog(api, prod_list, json_data):
    if not json_data:
        return
    for prod_data in json_data:
        product = api.get_product(prod_data["id"])
        product.load_gog_min(prod_data)
        prod_list.append(product)

def add_products_glx(api, prod_list, json_data):
    if not json_data:
        return
    for prod_data in json_data:
        product = api.get_product(prod_data["id"])
        product.load_glx(prod_data)
        prod_list.append(product)



class Product:
    def __init__(self, api, product_id, slug=None):
        self.loaded = set()
        self.api = api
        self.id = int(product_id)
        if slug is not None:
            self.slug = slug

    def load_glx(self, data):
        self.title = data["title"]
        self.slug = data["slug"]
        self.content_systems = parse_systems(
            data["content_system_compatibility"])
        self.languages = list(data["languages"].keys())
        self.link_purchase = data["links"]["purchase_link"]
        self.link_card = data["links"]["product_card"]
        self.link_support = data["links"]["support"]
        self.link_forum = data["links"]["forum"]
        self.in_development = data["in_development"]["active"]
        self.development_until = maybe_timestamp(
            data["in_development"]["until"])
        self.is_secret = data["is_secret"]
        self.game_type = data["game_type"]
        self.is_pre_order = data["is_pre_order"]
        self.store_date = maybe_timestamp(data["release_date"])
        self.image_background = data["images"]["background"]
        self.image_logo = data["images"]["logo"]
        self.image_logo_2x = data["images"]["logo2x"]
        self.image_icon = data["images"].get("icon")
        self.image_sidebar_icon = data["images"]["sidebarIcon"]
        self.image_sidebar_icon_2x = data["images"]["sidebarIcon2x"]
        if data["dlcs"]:
            self.dlcs = [
                self.api.get_product(dlc["id"])
                for dlc in data["dlcs"]["products"]]
        else:
            self.dlcs = []

        # Expanded

        if "downloads" in data:
            self.installers = [Download(self.api, dl_data)
                for dl_data in data["downloads"]["installers"]]
            self.patches = [Download(self.api, dl_data)
                for dl_data in data["downloads"]["patches"]]
            self.language_packs = [Download(self.api, dl_data)
                for dl_data in data["downloads"]["language_packs"]]
            self.bonus_content = [Download(self.api, dl_data)
                for dl_data in data["downloads"]["bonus_content"]]
        else:
            self.installers = None
            self.patches = None
            self.language_packs = None
            self.bonus_content = None

        if "expanded_dlcs" in data:
            self.dlcs = []
            add_products_glx(self.api, self.dlcs, data["expanded_dlcs"])
        else:
            self.dlcs = None

        if "description" in data:
            self.description = data["description"]["full"]
            self.description_lead = data["description"]["lead"]
            self.cool_about_it = data["description"]["whats_cool_about_it"]
        else:
            self.description = None
            self.description_lead = None
            self.cool_about_it = None

        if "screenshots" in data:
            self.screenshots = data["screenshots"]
        else:
            self.screenshots = None

        if "videos" in data:
            self.videos = data["videos"]
        else:
            self.videos = None

        if "related_products" in data:
            self.related_products = []
            add_products_glx(
                self.api, self.related_products, data["related_products"])
        else:
            self.related_products = None

        if "changelog" in data:
            self.changelog = data["changelog"]
        else:
            self.changelog = None

        self.loaded.add("glx")

    def load_gog_min(self, data):
        self.game_type = GOGDATA_TYPE[data["type"]]
        self.is_coming_soon = data["isComingSoon"]
        self.in_development = data["isInDevelopment"]
        self.slug = data["slug"]
        self.link_forum = data["forumUrl"]
        self.original_category = data["originalCategory"]
        self.is_available = data["availability"]["isAvailable"]
        self.is_available_in_account = \
            data["availability"]["isAvailableInAccount"]
        self.is_game = data["isGame"]
        self.release_date = maybe_timestamp(data["releaseDate"])
        self.price = parse_price(data["price"])
        self.link_support = data["supportUrl"]
        self.category = data["category"]
        self.is_discounted = data["isDiscounted"]
        self.custom_attributes = data.get("customAttributes", []) # optional
        self.developer = data.get("developer") # missing in series
        self.rating = data["rating"]
        self.is_movie = data["isMovie"]
        self.buyable = data["buyable"]
        self.publisher = data.get("publisher") # missing in series
        #self.sales_visibility IGNORED
        self.title = data["title"]
        self.image_logo = data["image"]
        self.link_card = data["url"]
        self.is_price_visible = data["isPriceVisible"]
        self.systems = parse_systems(data["worksOn"])

        self.loaded.add("gog_min")

    def load_gog(self, data):
        self.load_gog_min(data)

        self.image_background = data["backgroundImageSource"] + ".jpg"
        self.seo_description = data["cardSeoDescription"]
        if data["series"]:
            self.series = Series(self.api, data["series"])
        else:
            self.series = None
        self.required_products = []
        add_products_gog(
            self.api, self.required_products, data["requiredProducts"])
        #self.media IGNORED
        #self.videos IGNORED
        self.dlcs = []
        add_products_gog(self.api, self.dlcs, data["dlcs"])
        self.cool_about_it = data["whatsCoolAboutIt"]
        if data["screenshots"]:
            self.screenshot_ids = list(data["screenshots"].keys())
        else:
            self.screenshot_ids = None
        self.votes_count = data["votesCount"]
        self.languages_str = data["languages"]
        #self.notification IGNORED
        self.brand_ratings = data["brandRatings"]
        self.children = []
        add_products_gog(self.api, self.children, data["children"])
        self.os_requirements = parse_system_reqs(data["osRequirements"])
        self.system_requirements = parse_system_reqs(
            data["systemRequirements"])
        self.recommendations = []
        add_products_gog(
            self.api, self.recommendations, data["recommendations"]["all"])
        # self.bonus_content TODO
        self.image_background_bw = data["backgroundImage"]
        self.image_logo_facebook = data["imageLogoFacebook"]
        self.copyrights = data["copyrights"]
        # self.reviews TODO
        self.reviewable = data["canBeReviewed"]
        self.parents = []
        add_products_gog(self.api, self.parents, data["parents"])
        self.extra_requirements = data["extraRequirements"]
        self.packs = []
        add_products_gog(self.api, self.packs, data["packs"])
        self.download_size = data["downloadSize"]
        self.genres = data["genres"]
        self.features = data["features"]
        self.seo_keywords = data["cardSeoKeywords"]
        self.description = data["description"]["full"]
        self.description_lead = data["description"]["lead"]

        self.loaded.add("gog")

    def update_glx(self):
        data = self.api.galaxy_product(self.id)
        self.load_glx(data)

    def update_glx_ext(self):
        data = self.api.galaxy_product(self.id, expand=True)
        self.load_glx(data)

    def update_gog(self):
        data = self.api.web_game_gogdata(self.slug)["gameProductData"]
        self.load_gog(data)

    def get_builds(self, system):
        # TODO: return counts and has_private_branches
        data = self.api.galaxy_builds(self.id, system)
        return [Build(self.api, build_data) for build_data in data["items"]]

    def __repr__(self):
        return "<Product id={}>".format(self.id)


class Price:
    def __init__(self, base, final, symbol, promo_id):
        self.base = base
        self.final = final
        self.symbol = symbol
        self.promo_id = promo_id

    @property
    def discount(self):
        return (self.final / self.base) * 100

    @property
    def discount_amount(self):
        return self.base - self.final

    @property
    def is_discounted(self):
        return self.final != self.base

    @property
    def is_free(self):
        return self.final == Decimal(0)

    def __repr__(self):
        return "Price(base={!r}, final={!r}, symbol={!r}, promo_id={!r})"

class Series:
    def __init__(self, api, series_data):
        self.api = api
        self.load_series(series_data)

    def load_series(self, series_data):
        self.id = series_data["id"]
        self.name = series_data["name"]
        self.price = parse_price(series_data["price"])
        self.products = []
        add_products_gog(self.api, self.products, series_data["products"])

    def __repr__(self):
        return "<Series id={!r} name={!r} price={!r} products={!r}>".format(
            self.id, self.name, self.price, self.products)
