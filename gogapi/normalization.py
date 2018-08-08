from gogapi import names



GOG_TO_IETF = {
    "brazilian": "pt-BR",
    "brazilian-portuguese": "pt-BR",
    "czech": "cs-CZ",
    "english": "en-US",
    "french": "fr-FR",
    "german": "de-DE",
    "hungarian": "hu-HU",
    "italian": "it-IT",
    "japanese": "ja-JP",
    "neutral": "*",
    "polish": "pl-PL",
    "portuguese": "pt-PT",
    "russian": "ru-RU",
    "slovak": "sk-SK",
    "spanish": "es-ES",

    "ar": "ar-SA",
    "be": "be-BY",
    "bl": "bg-BG",
    "br": "pt-BR",
    "ca": "ca-ES",
    "cn": "zh-CN",
    "cz": "cs-CZ",
    "da": "da-DK",
    "de": "de-DE",
    "en": "en-US",
    "es": "es-ES",
    "es_mx": "es-MX",
    "fa": "fa-IR",
    "fi": "fi-FI",
    "fr": "fr-FR",
    "gk": "el-GR",
    "gog_in": "iu-CA",
    "hu": "hu-HU",
    "is": "is-IS",
    "it": "it-IT",
    "jp": "ja-JP",
    "ko": "ko-KR",
    "nl": "nl-NL",
    "no": "no-NO",
    "pl": "pl-PL",
    "pt": "pt-PT",
    "ro": "ro-RO",
    "ru": "ru-RU",
    "sb": "sr-RS",
    "sk": "sk-SK",
    "sv": "sv-SE",
    "th": "th-TH",
    "tr": "tr-TR",
    "uk": "uk-UA",
    "zh_hans": "zh-Hans-CN",
    "zh-hans": "zh-Hans-CN",
    "zh_hant": "zh-Hant-CN"
}


def normalize_language(lang):
    if lang in names.IETF_CODES:
        return lang
    for ietf_code in names.IETF_CODES.keys():
        if lang.lower() == ietf_code.lower():
            return ietf_code
    if lang.lower() in GOG_TO_IETF:
        return GOG_TO_IETF[lang.lower()]
    return lang


def normalize_system(system_name):
    system_name = system_name.lower()
    if system_name == "osx":
        return "mac"
    else:
        return system_name
