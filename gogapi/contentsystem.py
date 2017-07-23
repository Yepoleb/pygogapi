from gogapi.meta import GOGBase, Property

class DepotFile:
    def __init__(self, api, file_data):
        self.api = api
        self.load_glx(file_data)

    def load_glx(self, file_data):
        self.url = file_data["url"]
        self.size = file_data["size"]
        self.checksum = file_data["hash"]
        self.path = file_data["path"]
        self.offset = file_data["offset"]

class Depot(GOGBase):
    version = Property("manifest")
    name = Property("manifest")
    files = Property("manifest")

    def __init__(self, api, url, depot_data):
        super().__init__()
        self.api = api
        self.url = url
        self.load_depot(depot_data)

    def load_depot(self, depot_data):
        self.languages = depot_data["languages"]
        self.size = int(depot_data["size"])
        self.game_ids = depot_data["gameIDs"]
        self.systems = depot_data["systems"]
        self.manifest_name = depot_data["manifest"]

    def load_manifest(self, manifest_data):
        self.version = manifest_data["version"]
        self.name = manifest_data["depot"]["name"]
        self.files = [
            DepotFile(self.api, file_data)
            for file_data in manifest_data["depot"]["files"]]

    def update_manifest(self):
        manifest_data = self.api.get_json(self.manifest_url)
        self.load_manifest(manifest_data)

    @property
    def manifest_id(self):
        assert self.manifest_name.endswith(".json")
        return self.manifest_name[:-len(".json")]

    @property
    def manifest_url(self):
        # Remove file part from url and replace it with the manifest
        return self.url[:self.url.rfind('/') + 1] + self.manifest_name


class Redist:
    def __init__(self, api, redist_data):
        self.api = api
        self.load_glx(redist_data)

    def load_glx(self, redist_data):
        self.redist = redist_data["redist"]
        self.executable = redist_data["executable"]
        self.argument = redist_data["argument"]
        self.size = redist_data["size"]


class Repository:
    def __init__(self, api, url, repo_data):
        product_data = repo_data["product"]
        self.api = api
        self.url = url
        self.timestamp = product_data["timestamp"] # TODO: parse
        self.depots = []
        self.redists = []
        for depot_data in product_data["depots"]:
            if "manifest" in depot_data:
                self.depots.append(Depot(self.api, self.url, depot_data))
            else:
                self.redists.append(Redist(self.api, depot_data))
        self.support_commands = product_data["support_commands"] # TODO: classify
        self.install_directory = product_data["installDirectory"]
        self.root_game_id = product_data["rootGameID"]
        self.game_ids = product_data["gameIDs"] # TODO: classify
        self.project_name = product_data["projectName"]
        self.version = repo_data["version"]


class Build(GOGBase):
    repository = Property("repo")

    def __init__(self, api, build_data):
        super().__init__()
        self.api = api
        self.id = build_data["build_id"]
        self.product_id = build_data["product_id"]
        self.os = build_data["os"] # TODO: verify format
        self.branch = build_data["branch"]
        self.version_name = build_data["version_name"]
        self.tags = build_data["tags"]
        self.public = build_data["public"]
        self.date_published = build_data["date_published"]
        self.generation = build_data["generation"]
        self.link = build_data["link"]
        self.legacy_build_id = build_data.get("legacy_build_id", None)

    def load_repo(self, repo_data):
        self.repository = Repository(self.api, self.link, repo_data)

    def update_repo(self):
        if self.generation == 1:
            repo_data = self.api.get_json(self.link, authorized=False)
            self.load_repo(repo_data)
        else:
            raise NotImplementedError()
