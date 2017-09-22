from gogapi import GogApi, Token

token = Token.from_file("token.json")
if token.expired():
    token.refresh()
    token.save("token.json")

api = GogApi(token)

prod = api.get_product(2134842136)
prod.update_galaxy(expand=True)
print("Updated", prod.title)
