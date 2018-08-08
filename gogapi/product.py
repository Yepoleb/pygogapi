from datetime import datetime
import itertools
import string
from decimal import Decimal
import re

import dateutil.parser

from gogapi.contentsystem import Build, SecureLinkV2
from gogapi.download import Download
from gogapi.normalization import normalize_system, normalize_language
from gogapi.base import GogObject, MissingResourceError, logger

GOGDATA_TYPE = {
    1: "game",
    2: "pack",
    3: "dlc"
}

YOUTUBE_EMBED_RE = re.compile("youtube.com/embed/([\w\-_]+)")



def parse_systems(system_compat):
    return set(
        normalize_system(system)
        for system, supported in system_compat.items() if supported)

def parse_system_reqs(system_reqs):
    if not system_reqs:
        return None
    else:
        return {
            normalize_system(system): reqs
            for system, reqs in system_reqs.items()}

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

def make_slug(name):
    return "".join(c for c in name.lower() if c in string.ascii_lowercase)

def remove_duplicates(l, key):
    new_l = []
    for item in l:
        if not key(item):
            continue
        if key(item) not in list(key(x) for x in new_l):
            new_l.append(item)

    return new_l


def add_products_web(api, prod_list, json_data):
    if not json_data:
        return
    for prod_data in json_data:
        product = api.product(prod_data["id"])
        product.load_web_min(prod_data)
        prod_list.append(product)

def add_products_galaxy(api, prod_list, json_data):
    if not json_data:
        return
    for prod_data in json_data:
        product = api.product(prod_data["id"])
        product.load_galaxy(prod_data)
        prod_list.append(product)

def parse_genres(api, genres_data):
    genre_list = []
    added_genres = set()
    for genre_data in genres_data:
        name, slug = genre_data["name"], genre_data["slug"]
        if not name:
            continue
        if not slug:
            slug = make_slug(name)
        if slug in added_genres:
            continue
        else:
            genre_list.append(Genre(api, name, slug))
            added_genres.add(slug)

    return genre_list

def parse_features(api, features_data):
    feature_list = []
    added_features = set()
    for feature_data in features_data:
        name, slug = feature_data["title"], feature_data["slug"]
        if not name:
            continue
        if not slug:
            slug = make_slug(name)
        if slug in added_features:
            continue
        else:
            feature_list.append(Feature(api, name, slug))
            added_features.add(slug)

    return feature_list


class Product(GogObject):
    def __init__(self, api, product_id, slug=None):
        super().__init__(api)
        self.id = int(product_id)
        if slug is not None:
            self.slug = slug

    def from_galaxy(data):
        prod = Product(data["id"])
        prod.load_galaxy(data)
        return prod

    def from_web(data):
        prod = Product(data["id"])
        prod.load_web(data)
        return prod

    def from_web_min(data):
        prod = Product(data["id"])
        prod.load_web_min(data)
        return prod

    def load_galaxy(self, data):
        logger.debug("Loading galaxy data for %s", self.id)
        self.title_galaxy = data["title"]
        self.slug = data["slug"]
        self.content_systems = parse_systems(
            data["content_system_compatibility"])

        if data["languages"]:
            self.languages = [
                Language(self.api, name, normalize_language(isocode))
                for isocode, name in data["languages"].items()]
        else:
            self.languages = []
        self.in_development = data["in_development"]["active"]
        self.development_until = maybe_timestamp(
            data["in_development"]["until"])
        self.is_secret = data["is_secret"]
        self.type = data["game_type"]
        self.is_pre_order = data["is_pre_order"]
        self.store_date = maybe_timestamp(data["release_date"])

        self.link_purchase = data["links"]["purchase_link"]
        self.link_card = data["links"]["product_card"]
        self.link_support = data["links"]["support"]
        self.link_forum = data["links"]["forum"]

        self.image_background = data["images"]["background"]
        self.image_logo = data["images"]["logo"]
        self.image_logo_2x = data["images"]["logo2x"]
        self.image_icon = data["images"].get("icon")
        self.image_sidebar_icon = data["images"]["sidebarIcon"]
        self.image_sidebar_icon_2x = data["images"]["sidebarIcon2x"]

        if data.get("dlcs", False):
            self.dlcs = [
                self.api.product(dlc["id"])
                for dlc in data["dlcs"]["products"]]
        else:
            self.dlcs = []

        # Expanded

        if "downloads" in data:
            self.installers = [Download(self.api, "installers", dl_data)
                for dl_data in data["downloads"]["installers"]]
            self.patches = [Download(self.api, "patches", dl_data)
                for dl_data in data["downloads"]["patches"]]
            self.language_packs = [Download(self.api, "language_packs", dl_data)
                for dl_data in data["downloads"]["language_packs"]]
            self.bonus_content = [Download(self.api, "bonus_content", dl_data)
                for dl_data in data["downloads"]["bonus_content"]]
            self.loaded.add("downloads")

        if "expanded_dlcs" in data:
            self.dlcs = []
            add_products_galaxy(self.api, self.dlcs, data["expanded_dlcs"])
            self.loaded.add("expanded_dlcs")

        if "description" in data:
            self.description = data["description"]["full"]
            self.description_lead = data["description"]["lead"]
            self.cool_about_it = data["description"]["whats_cool_about_it"]
            self.loaded.add("description")

        if "screenshots" in data:
            self.screenshots = [screenshot_data["image_id"]
                for screenshot_data in data["screenshots"]]
            self.loaded.add("screenshots")

        if "videos" in data:
            self.videos = [Video(self.api, video_data)
                for video_data in data["videos"]]
            self.loaded.add("videos")

        if "related_products" in data:
            self.related_products = []
            add_products_galaxy(
                self.api, self.related_products, data["related_products"])
            self.loaded.add("related_products")

        if "changelog" in data:
            self.changelog = data["changelog"]
            self.loaded.add("changelog")

        self.loaded.add("galaxy")

    def load_web_min(self, data):
        self.type = GOGDATA_TYPE[data["type"]]
        self.is_coming_soon = data["isComingSoon"]
        self.in_development = data["isInDevelopment"]
        if data["slug"]:
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
        self.title_web = data["title"]
        self.image_logo = data["image"]
        self.link_card = data["url"]
        self.is_price_visible = data["isPriceVisible"]
        self.systems = parse_systems(data["worksOn"])

        self.loaded.add("web_min")

    def load_web(self, data):
        logger.debug("Loading web data for %s", self.id)
        self.load_web_min(data)

        self.image_background = data["backgroundImageSource"] + ".jpg"
        self.seo_description = data["cardSeoDescription"]
        if data["series"]:
            self.series = Series(self.api, data["series"])
        else:
            self.series = None
        self.required_products = []
        add_products_web(
            self.api, self.required_products, data["requiredProducts"])
        #self.media IGNORED
        #self.videos IGNORED
        self.dlcs = []
        add_products_web(self.api, self.dlcs, data["dlcs"])
        self.cool_about_it = data["whatsCoolAboutIt"] or None
        if data["screenshots"]:
            self.screenshot_ids = list(data["screenshots"].keys())
        else:
            self.screenshot_ids = None
        self.votes_count = data["votesCount"]
        self.languages_str = data["languages"]
        #self.notification IGNORED
        self.brand_ratings = data["brandRatings"]
        self.children = []
        add_products_web(self.api, self.children, data["children"])
        self.os_requirements = parse_system_reqs(data["osRequirements"])
        self.system_requirements = parse_system_reqs(
            data["systemRequirements"])
        self.recommendations = []
        add_products_web(
            self.api, self.recommendations, data["recommendations"]["all"])
        # self.bonus_content IGNORED
        self.image_background_bw = data["backgroundImage"]
        self.image_logo_facebook = data["imageLogoFacebook"]
        self.copyrights = data["copyrights"]
        self.reviews = Reviews(self.api, data["reviews"])
        self.reviewable = data["canBeReviewed"]
        self.parents = []
        add_products_web(self.api, self.parents, data["parents"])
        self.extra_requirements = data["extraRequirements"]
        self.packs = []
        add_products_web(self.api, self.packs, data["packs"])
        self.download_size = data["downloadSize"]
        self.genres = parse_genres(self.api, data["genres"])
        self.features = parse_features(self.api, data["features"])
        self.seo_keywords = data["cardSeoKeywords"]
        self.description = data["description"]["full"] or None
        self.description_lead = data["description"]["lead"] or None

        self.loaded.add("web")

    def update_galaxy(self, expand=False):
        data = self.api.galaxy_product(self.id, expand=expand)
        self.load_galaxy(data)

    def update_web(self):
        logger.debug("Updating web %s", self.id)
        gogdata = self.api.web_game_gogdata(self.slug)
        if "gameProductData" in gogdata:
            self.load_web(gogdata["gameProductData"])
        else:
            raise MissingResourceError(
                "{} is missing gameProductData".format(self.slug))

    def get_builds(self, system):
        # TODO: return counts and has_private_branches
        if system == "mac":
            system = "osx"

        data = self.api.galaxy_builds(self.id, system)
        builds_dirty = [Build(self.api, build_data) for build_data in data["items"]]
        builds_dedup = {build.id: build for build in builds_dirty}
        return list(builds_dedup.values())

    def get_secure_link(self, path, generation):
        link_data = self.api.galaxy_secure_link(self.id, path, generation)
        if generation == 1:
            raise NotImplementedError("V1 not implemented")
        elif generation == 2:
            return SecureLinkV2(self.api, link_data)

    @property
    def required_product(self):
        if self.required_products:
            return self.required_products[0]
        else:
            return None

    @property
    def downloads(self):
        return itertools.chain(
            self.installers, self.patches, self.language_packs,
            self.bonus_content)

    @property
    def forum_slug(self):
        return self.link_forum.rsplit('/', 1)[1]

    @property
    def title(self):
        return self.title_galaxy or self.title_web

    def __repr__(self):
        return self.simple_repr(["id", "slug", "title", "type"])



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


class Series(GogObject):
    def __init__(self, api, series_data):
        super().__init__(api)
        self.load_series(series_data)

    def load_series(self, series_data):
        self.id = series_data["id"]
        self.name = series_data["name"]
        self.price = parse_price(series_data["price"])
        self.products = []
        add_products_web(self.api, self.products, series_data["products"])

    def __repr__(self):
        return "<Series id={!r} name={!r} price={!r} products={!r}>".format(
            self.id, self.name, self.price, self.products)


class Reviews(GogObject):
    def __init__(self, api, reviews_data):
        super().__init__(api)
        self.load_reviews(reviews_data)

    def load_reviews(self, reviews_data):
        self.total_results = int(reviews_data["totalResults"])
        self.total_pages = reviews_data["totalPages"]
        self.entries = []
        for page in reviews_data["pages"]:
            for review_entry in page:
                self.entries.append(Review(self.api, review_entry))


class Review(GogObject):
    def __init__(self, api, review_data):
        super().__init__(api)

    def load_review(self, review_data):
        pass # TODO: implement


class Feature(GogObject):
    def __init__(self, api, name, slug):
        super().__init__(api)
        self.name = name
        self.slug = slug

    def __repr__(self):
        return self.simple_repr(["name", "slug"])

class Genre(GogObject):
    def __init__(self, api, name, slug):
        super().__init__(api)
        self.name = name
        self.slug = slug

    def __repr__(self):
        return self.simple_repr(["name", "slug"])

class Language(GogObject):
    def __init__(self, api, name, isocode):
        super().__init__(api)
        self.name = name
        self.isocode = isocode

    def __repr__(self):
        return self.simple_repr(["name", "isocode"])

class Video(GogObject):
    def __init__(self, api, data):
        super().__init__(api)
        self.load_video(data)

    def load_video(self, data):
        self.video_url = data["video_url"]
        self.thumbnail_url = data["thumbnail_url"]
        self.provider = data["provider"]

    @property
    def video_id(self):
        if self.provider != "youtube":
            raise NotImplementedError(
                "Providers other than youtube are not implemented")
        else:
            return YOUTUBE_EMBED_RE.search(self.video_url).group(1)
