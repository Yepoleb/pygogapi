import webbrowser
import re

from gogapi import Token, get_auth_url


LOGIN_INSTRUCTIONS = """\
Your web browser has been opened to allow you to log in.
If that did not work, please manually open {auth_url}
After completing the login you will be redirected to a blank page. Copy the
full URL starting with https://embed.gog.com/on_login_success and paste it
into this window.
"""

LOGIN_CODE_RE = re.compile(r"code=([\w\-]+)")

webbrowser.open_new_tab(get_auth_url())
print(LOGIN_INSTRUCTIONS.format(auth_url=get_auth_url()))
login_url = input("Login URL: ")
code_match = LOGIN_CODE_RE.search(login_url)
if code_match is None:
    print("Error: Could not find a login code in the provided URL")
    exit(1)
login_code = code_match.group(1)
token = Token.from_code(login_code)
# TODO: Get file name from argv
token.save("token.json")
print("Token saved as token.json")
