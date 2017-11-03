from gogapi.base import GogObject

class SearchResult(GogObject):
    def __init__(self, api, query, search_data):
        super().__init__(api)
        self.query = query
        self.load_search(search_data)

    def load_search(self, search_data):
        self.products = []
        for product_data in search_data["products"]:
            product = self.api.product(product_data["id"])
            product.load_web_min(product_data)
            self.products.append(product)

        self.page = int(search_data["page"])
        self.total_pages = search_data["totalPages"]
        self.total_results = int(search_data["totalResults"])
        self.total_games_found = search_data["totalGamesFound"]
        self.total_movies_found = search_data["totalMoviesFound"]

    def next_page(self):
        assert self.page < self.total_pages
        new_query = self.query.copy()
        new_query["page"] = self.page + 1
        return self.api.search(**new_query)

    def previous_page(self):
        assert self.page > 0
        new_query = self.query.copy()
        new_query["page"] = self.page - 1
        return self.api.search(**new_query)

    def iter_pages(self):
        page = self
        yield page
        while not page.last_page:
            page = page.next_page()
            yield page

    def iter_products(self):
        for page in self.iter_pages():
            for product in page.products:
                yield product

    @property
    def count(self):
        return len(self.products)

    @property
    def first_page(self):
        return self.page == 1

    @property
    def last_page(self):
        return self.page == self.total_pages

    def __repr__(self):
        return self.simple_repr(
            ["page", "total_pages", "total_results", "total_games_found",
            "total_movies_found", "products"])
