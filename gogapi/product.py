import arrow
from decimal import Decimal

from gogapi.meta import GOGBase, Property
from gogapi.contentsystem import Build

def parse_systems_glx(system_compat):
    systems = []
    if system_compat["windows"]:
        systems.append("windows")
    if system_compat["osx"]:
        systems.append("mac")
    if system_compat["linux"]:
        systems.append("linux")
    return systems

def parse_systems_gog(system_compat):
    systems = []
    if system_compat["Windows"]:
        systems.append("windows")
    if system_compat["Mac"]:
        systems.append("mac")
    if system_compat["Linux"]:
        systems.append("linux")
    return systems

def parse_os_reqs(os_reqs):
    return {
        "windows": os_reqs["Windows"],
        "mac": os_reqs["Mac OS X"],
        "linux": os_reqs["Linux"]
    }

def parse_system_reqs(system_reqs):
    return {
        "windows": system_reqs["windows"],
        "mac": system_reqs["osx"],
        "linux": system_reqs["linux"]
    }

def parse_price(price_data):
    return Price(
        base=Decimal(price_data["baseAmount"]),
        final=Decimal(price_data["finalAmount"]),
        symbol=price_data["symbol"],
        promo_id=price_data.get("promoId", None)
    )

def parse_series(api, series_data):
    series = api.get_series(series_data["id"])
    self.series.load_gog(data["series"])
    api.add_products_gog(series.products, series_data["products"])
    return series

def maybe_timestamp(timestamp):
    if timestamp:
        return arrow.get(timestamp)
    else:
        return None

GOGDATA_TYPE = {
    1: "game",
    2: "pack",
    3: "dlc"
}



class Product(GOGBase):
    title = Property("glx", "gog")
    slug = Property("glx", "gog")
    game_type = Property("glx", "gog")
    description = Property("glx_ext", "gog")
    description_lead = Property("glx_ext", "gog")
    cool_about_it = Property("glx_ext", "gog")
    image_background = Property("glx", "gog")
    image_logo = Property("glx", "gog")
    link_card = Property("glx", "gog")
    link_forum = Property("glx", "gog")
    link_support = Property("glx", "gog")
    in_development = Property("glx", "gog")
    dlcs = Property("glx", "gog")

    #bonus_content = Property("gog")
    brand_ratings = Property("gog")
    buyable = Property("gog")
    category = Property("gog")
    changelog = Property("glx_ext")
    children = Property("gog")
    content_systems = Property("glx")
    copyrights = Property("gog")
    custom_attributes = Property("gog")
    developer = Property("gog")
    development_until = Property("glx")
    download_size = Property("gog")
    installers = Property("glx_ext")
    patches = Property("glx_ext")
    #language_packs = Property("glx_ext")
    bonus_content = Property("glx_ext")
    extra_requirements = Property("gog")
    features = Property("gog")
    genres = Property("gog")
    image_background_bw = Property("gog")
    image_logo_facebook = Property("gog")
    image_icon = Property("glx")
    image_logo_2x = Property("glx")
    image_sidebar_icon = Property("glx")
    image_sidebar_icon_2x = Property("glx")
    is_available = Property("gog")
    is_available_in_account = Property("gog")
    is_coming_soon = Property("gog")
    is_discounted = Property("gog")
    is_game = Property("gog")
    is_movie = Property("gog")
    is_pre_order = Property("glx")
    is_price_visible = Property("gog")
    is_secret = Property("glx")
    languages = Property("glx")
    languages_str = Property("gog")
    link_purchase = Property("glx")
    #media = Property("gog")
    #notification = Property("gog")
    original_category = Property("gog")
    os_requirements = Property("gog")
    packs = Property("gog")
    parents = Property("gog")
    price = Property("gog")
    publisher = Property("gog")
    rating = Property("gog")
    recommendations = Property("gog")
    related_products = Property("glx_ext")
    release_date = Property("gog")
    #required_products = Property("gog")
    reviewable = Property("gog")
    #reviews = Property("gog")
    #sales_visibility = Property("gog")
    screenshot_ids = Property("gog")
    screenshots = Property("glx_ext")
    seo_description = Property("gog")
    seo_keywords = Property("gog")
    series = Property("gog")
    store_date = Property("glx")
    system_requirements = Property("gog")
    systems = Property("gog")
    videos = Property("glx_ext")
    votes_count = Property("gog")

    def __init__(self, api, product_id, slug=None):
        super().__init__()
        self.api = api
        self.id = product_id
        if slug is not None:
            self.slug = slug

    def load_glx(self, data):
        self.title = data["title"]
        self.slug = data["slug"]
        self.content_systems = parse_systems_glx(
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
        self.image_icon = data["images"]["icon"]
        self.image_sidebar_icon = data["images"]["sidebarIcon"]
        self.image_sidebar_icon_2x = data["images"]["sidebarIcon2x"]
        self.dlcs = []
        if "dlcs" in data:
            for dlc in data["dlcs"]["products"]:
                self.dlcs.append(self.api.get_product(dlc["id"]))

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
        if "expanded_dlcs" in data:
            self.dlcs = []
            self.api.add_products_glx(self.dlcs, data["expanded_dlcs"])
        if "description" in data:
            self.description = data["description"]["full"]
            self.description_lead = data["description"]["lead"]
            self.cool_about_it = data["description"]["whats_cool_about_it"]
        if "screenshots" in data:
            self.screenshots = data["screenshots"]
        if "videos" in data:
            self.videos = data["videos"]
        if "related_products" in data:
            self.related_products = []
            self.api.add_products_glx(
                self.related_products, data["related_products"])
        if "changelog" in data:
            self.changelog = data["changelog"]

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
        self.release_date = arrow.get(data["releaseDate"])
        self.price = parse_price(data["price"])
        self.link_support = data["supportUrl"]
        self.category = data["category"]
        self.is_discounted = data["isDiscounted"]
        self.custom_attributes = data.get("customAttributes", []) # optional
        self.developer = data["developer"]
        self.rating = data["rating"]
        self.is_movie = data["isMovie"]
        self.buyable = data["buyable"]
        self.publisher = data["publisher"]
        #self.sales_visibility IGNORED
        self.title = data["title"]
        self.image_logo = data["image"]
        self.link_card = data["url"]
        self.is_price_visible = data["isPriceVisible"]
        self.systems = parse_systems_gog(data["worksOn"])

    def load_gog(self, data):
        self.image_background = data["backgroundImageSource"] + ".jpg"
        self.seo_description = data["cardSeoDescription"]
        self.series = parse_series(self.api, data["series"])
        self.required_products = []
        self.api.add_products_gog(
            self.required_products, data["requiredProducts"])
        #self.media IGNORED
        #self.videos IGNORED
        self.dlcs = []
        self.api.add_products_gog(self.dlcs, data["dlcs"])
        self.cool_about_it = data["whatsCoolAboutIt"]
        self.screenshot_ids = list(data["screenshots"].keys())
        self.votes_count = data["votesCount"]
        self.languages_str = data["languages"]
        #self.notification IGNORED
        self.brand_ratings = data["brandRatings"]
        self.children = []
        self.api.add_products_gog(self.children, data["children"])
        self.os_requirements = parse_os_reqs(data["osRequirements"])
        self.system_requirements = parse_system_reqs(
            data["systemRequirements"])
        self.recommendations = []
        self.api.add_products_gog(
            self.recommendations, data["recommendations"]["all"])
        # self.bonus_content TODO
        self.image_background_bw = data["backgroundImage"]
        self.image_logo_facebook = data["imageLogoFacebook"]
        self.copyrights = data["copyrights"]
        # self.reviews TODO
        self.reviewable = data["canBeReviewed"]
        self.parents = []
        self.api.add_products_gog(self.parents, data["parents"])
        self.extra_requirements = data["extraRequirements"]
        self.packs = []
        self.api.add_products_gog(self.packs, data["packs"])
        self.download_size = data["downloadSize"]
        self.genres = data["genres"]
        self.features = data["features"]
        self.seo_keywords = data["SeoKeywords"]
        self.description = data["description"]["full"]
        self.description_lead = data["description"]["lead"]

    def update_glx(self):
        data = self.api.galaxy_product(self.id)
        self.load_glx(data)

    def update_glx_ext(self):
        data = self.api.galaxy_product(self.id, expand=True)
        self.load_glx(data)

    def update_gog(self):
        data = self.api.web_games_gogdata(self.slug)
        self.load_gog(data)

    def get_builds(self, system):
        # TODO: return counts and has_private_branches
        data = self.api.galaxy_builds(self.id, system)
        return [Build(self.api, build_data) for build_data in data["items"]]


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

class Series:
    def __init__(self, api, series_id):
        self.api = api
        self.id = series_id

    def load_gog(self, data):
        self.name = data["name"]
        self.price = parse_price(series_data["price"])
        self.products = []
        self.api.add_products_gog(self.products, data["products"])
