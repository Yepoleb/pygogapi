from gogapi.normalization import normalize_system
from gogapi.base import GogObject

# TODO: repr for everything


class Build(GogObject):
    def __init__(self, api, build_data):
        super().__init__(api)
        self.id = build_data["build_id"]
        self.product_id = int(build_data["product_id"])
        self.os = normalize_system(build_data["os"])
        self.branch = build_data["branch"]
        self.version_name = build_data["version_name"]
        self.tags = build_data["tags"]
        self.public = build_data["public"]
        self.date_published = build_data["date_published"]
        self.generation = build_data["generation"]
        self.link = build_data["link"]
        self.legacy_build_id = build_data.get("legacy_build_id", None)

    def load_repo_v1(self, repo_data):
        if self.generation != 1:
            raise Exception("Wrong generation: {}".format(self.generation))
        self.repository = RepositoryV1(self.api, self.link, repo_data)

        self.loaded.add("repo")

    def load_repo_v2(self, repo_data):
        if self.generation != 2:
            raise Exception("Wrong generation: {}".format(self.generation))
        self.repository = RepositoryV2(self.api, repo_data)

        self.loaded.add("repo")

    def update_repo(self):
        if self.generation == 1:
            repo_data = self.api.get_json(self.link, authorized=False)
            self.load_repo_v1(repo_data)
        elif self.generation == 2:
            repo_data = self.api.get_json(
                self.link, compressed=True, authorized=False)
            self.load_repo_v2(repo_data)
        else:
            raise NotImplementedError()

    def __repr__(self):
        return self.simple_repr([
            "id", "product_id", "os", "branch", "version_name", "tags",
            "public", "date_published", "generation", "link", "legacy_build_id"
        ])


########################################
# Generation 1
########################################

class RepositoryV1(GogObject):
    generation = 1

    def __init__(self, api, url, repo_data):
        super().__init__(api)
        self.url = url
        self.load_repo(repo_data)

    def load_repo(self, repo_data):
        product_data = repo_data["product"]
        # TODO: figure out what this is (doesn't look like a unix timestamp)
        self.timestamp = product_data["timestamp"]
        self.depots = []
        self.redists = []
        for depot_data in product_data["depots"]:
            if "manifest" in depot_data:
                self.depots.append(DepotV1(self.api, self.url, depot_data))
            else:
                self.redists.append(RedistV1(self.api, depot_data))
        self.support_commands = [
            SupportCommandV1(self.api, command_data)
            for command_data in product_data["support_commands"]]
        self.install_directory = product_data["installDirectory"]
        self.root_game_id = product_data["rootGameID"]
        self.game_ids = [
            RepositoryProductV1(self.api, product_data)
            for product_data in product_data["gameIDs"]]
        self.name = product_data["projectName"]
        assert repo_data["version"] == self.generation

    def __repr__(self):
        return self.simple_repr(
            ["url", "name", "timestamp", "install_directory"])


class RedistV1(GogObject):
    generation = 1

    def __init__(self, api, redist_data):
        super().__init__(api)
        self.load_galaxy(redist_data)

    def load_galaxy(self, redist_data):
        self.redist = redist_data["redist"]
        self.executable = redist_data["executable"]
        self.argument = redist_data["argument"]
        self.size = int(redist_data["size"])

    def __repr__(self):
        return self.simple_repr(["redist", "executable", "argument", "size"])


class RepositoryProductV1(GogObject):
    generation = 1

    def __init__(self, api, product_data):
        super().__init__(api)
        self.load_product(product_data)

    def load_product(self, product_data):
        self.dependencies = product_data["dependencies"] # TODO: investigate
        self.product_id = int(product_data["gameID"])
        self.names = product_data["name"]
        self.standalone = product_data["standalone"]

    def __repr__(self):
        return self.simple_repr(
            ["dependencies", "product_id", "names", "standalone"])


class SupportCommandV1(GogObject):
    generation = 1

    def __init__(self, api, command_data):
        super().__init__(api)
        self.load_command(command_data)

    def load_command(self, command_data):
        self.languages = command_data["languages"] # TODO: normalize
        self.executable = command_data["executable"]
        self.product_id = int(command_data["gameID"])
        self.systems = [
            normalize_system(system) for system in command_data["systems"]]
        self.argument = command_data["argument"]

class DepotV1(GogObject):
    generation = 1

    def __init__(self, api, url, depot_data):
        super().__init__(api)
        self.url = url
        self.load_depot(depot_data)

    def load_depot(self, depot_data):
        self.languages = depot_data["languages"] # TODO: normalize
        self.size = int(depot_data["size"])
        self.game_ids = [int(game_id) for game_id in depot_data["gameIDs"]]
        self.systems = [
            normalize_system(system) for system in depot_data["systems"]]
        self.manifest_name = depot_data["manifest"]

    def load_manifest(self, manifest_data):
        self.name = manifest_data["depot"]["name"]
        self.files = [
            DepotFileV1(self.api, file_data)
            for file_data in manifest_data["depot"]["files"]]
        assert manifest_data["version"] == self.generation

        self.loaded.add("manifest")

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

class DepotFileV1(GogObject):
    generation = 1

    def __init__(self, api, file_data):
        super().__init__(api)
        self.load_galaxy(file_data)

    def load_galaxy(self, file_data):
        self.url = file_data["url"]
        self.size = file_data["size"]
        self.checksum = file_data["hash"]
        self.path = file_data["path"]
        self.offset = file_data["offset"]


########################################
# Generation 2
########################################

class RepositoryV2(GogObject):
    generation = 2

    def __init__(self, api, repo_data):
        super().__init__(api)
        self.load_repo(repo_data)

    def load_repo(self, repo_data):
        self.base_product_id = int(repo_data["baseProductId"])
        self.client_id = repo_data.get("clientId")
        self.client_secret = repo_data.get("clientSecret")
        self.cloud_saves = repo_data.get("cloudSaves")
        self.dependencies = repo_data.get("dependencies", None)
        self.depots = [
            DepotV2(self.api, depot_data)
            for depot_data in repo_data["depots"]]
        self.install_directory = repo_data["installDirectory"]
        self.offline_depot = DepotV2(self.api, repo_data["offlineDepot"])
        self.platform = normalize_system(repo_data["platform"])
        self.products = [
            RepositoryProductV2(self.api, product_data)
            for product_data in repo_data["products"]]
        self.tags = repo_data.get("tags")
        assert repo_data["version"] == self.generation

    def __repr__(self):
        return self.simple_repr([
            "base_product_id", "client_id", "client_secret", "cloud_saves",
            "dependencies", "install_directory", "platform", "tags"
        ])


class RepositoryProductV2(GogObject):
    generation = 2

    def __init__(self, api, product_data):
        super().__init__(api)
        self.load_product(product_data)

    def load_product(self, product_data):
        self.name = product_data["name"]
        self.product_id = int(product_data["productId"])
        self.script = product_data.get("script", None)
        self.temp_arguments = product_data["temp_arguments"]
        self.temp_executable = product_data["temp_executable"]


class DepotV2(GogObject):
    generation = 2

    def __init__(self, api, depot_data):
        super().__init__(api)
        self.load_depot(depot_data)

    def load_depot(self, depot_data):
        self.compressed_size = depot_data["compressedSize"]
        self.size = depot_data["size"]
        self.languages = depot_data["languages"]
        self.manifest_id = depot_data["manifest"]
        self.product_id = int(depot_data["productId"])

    def load_manifest(self, manifest_data):
        self.items = []
        for depot_item in manifest_data["depot"]["items"]:
            if depot_item["type"] == "DepotFile":
                self.items.append(DepotFileV2(self.api, depot_item))
            elif depot_item["type"] == "DepotDirectory":
                self.items.append(DepotDirectoryV2(self.api, depot_item))
            else:
                raise NotImplementedError(
                    "Unknown depot item type: {}".format(depot_item["type"]))
        if "smallFilesContainer" in manifest_data["depot"]:
            self.small_files_container = DepotFileV2(
                self.api, manifest_data["depot"]["smallFilesContainer"])
        assert manifest_data["version"] == self.generation

        self.loaded.add("manifest")

    def update_manifest(self):
        manifest_data = self.api.galaxy_cs_meta(self.manifest_id)
        self.load_manifest(manifest_data)

    def __repr__(self):
        return self.simple_repr([
            "manifest_id", "product_id", "language", "size", "compressed_size"
        ])


class DepotFileV2(GogObject):
    generation = 2
    type = "DepotFile"

    def __init__(self, api, file_data):
        super().__init__(api)
        self.load_file(file_data)

    def load_file(self, file_data):
        self.chunks = [
            DepotChunkV2(self.api, chunk_data)
            for chunk_data in file_data["chunks"]]
        self.sfc_ref = file_data.get("sfcRef")
        self.flags = file_data.get("flags", [])
        self.path = file_data.get("path")
        self._md5 = file_data.get("md5")

    @property
    def checksum(self):
        if self._md5:
            return self._md5
        elif len(self.chunks) == 1:
            return self.chunks[0].md5
        else:
            return None

    @property
    def size(self):
        return sum(chunk.size for chunk in self.chunks)

    def __repr__(self):
        return self.simple_repr(["path"])


class DepotChunkV2(GogObject):
    generation = 2

    def __init__(self, api, chunk_data):
        super().__init__(api)
        self.load_chunk(chunk_data)

    def load_chunk(self, chunk_data):
        self.compressed_md5 = chunk_data["compressedMd5"]
        self.compressed_size = chunk_data["compressedSize"]
        self.md5 = chunk_data["md5"]
        self.size = chunk_data["size"]

    def __repr__(self):
        return self.simple_repr(
            ["compressed_md5", "compressed_size", "md5", "size"])


class DepotDirectoryV2(GogObject):
    generation = 2
    type = "DepotDirectory"

    def __init__(self, api, directory_data):
        super().__init__(api)
        self.load_directory(directory_data)

    def load_directory(self, directory_data):
        self.path = directory_data["path"]

    def __repr__(self):
        return self.simple_repr(["path"])


class SecureLinkV2(GogObject):
    generation = 2

    def __init__(self, api, link_data):
        super().__init__(api)
        self.load_link(link_data)

    def load_link(self, link_data):
        self.prod_id = link_data["product_id"]
        self.type = link_data["type"]
        self.full_url = link_data["url"]["url"]
        self.base_url = link_data["url"]["base_url"]
        self.path = link_data["url"]["path"]
        self.token = link_data["url"]["token"]

    def link_for(self, checksum):
        return "/".join((
            self.base_url, self.path, checksum[0:2], checksum[2:4], checksum
        )) + "?" + self.token

    def link_for_chunk(self, chunk):
        return self.link_for(chunk.compressed_md5)

    def __repr__(self):
        return self.simple_repr(
            ["prod_id", "type", "base_url", "path", "token"])
