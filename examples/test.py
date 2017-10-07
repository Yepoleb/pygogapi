from gogapi.base import GogObject
from gogapi import GogApi, Token, get_auth_url
import gogapi.api

token = Token.from_file("token.json")
if token.expired():
    token.refresh()
    token.save("token.json")

#gogapi.base.DEBUG_JSON = True
#token = None
api = GogApi(token)
print("User:", token.user_id)

#~ from pprint import pprint
prod = api.product(1275264927)
prod.update_galaxy(expand=True)
print(prod)
#~ for fileobj in prod.installers[0].files:
    #~ fileobj.update_chunklist()
    #~ print(fileobj.filename, fileobj.md5)
#~ builds = prod.get_builds("windows")
#~ print(builds[0].repository.depots[0].files[0].path)

# https://api.gog.com/products/2134842136?expand=downloads,expanded_dlcs,description,screenshots,videos,related_products,changelog&locale=en-US
#resp = api.get("https://api.gog.com/products/2134842136?expand=downloads,expanded_dlcs,description,screenshots,videos,related_products,changelog&locale=en-US", authorized=True)
#print(resp.status_code)
#print(resp.text)

#print(api.galaxy_achievements(1207659019))
