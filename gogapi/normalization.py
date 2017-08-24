def normalize_system(system_name):
    system_name = system_name.lower()
    if system_name == "osx":
        return "mac"
    else:
        return system_name

# TODO: Complete list
LANG_TO_LOCALE = {
    "English": "en",
    "German": "de",
    "French": "fr",
    "Italian": "it",
    "Spanish": "es",
}
