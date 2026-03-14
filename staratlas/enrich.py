import json
import os
import re

import pycountry


COMPANY_SUFFIX_RE = re.compile(r"\b(inc|llc|ltd|co|corp|corporation|company)\b", re.IGNORECASE)
NON_WORD_RE = re.compile(r"[^\w\s]")


COMMON_LOCATION_MAP = {
    "nyc": "US",
    "new york": "US",
    "san francisco": "US",
    "bay area": "US",
    "los angeles": "US",
    "seattle": "US",
    "austin": "US",
    "chicago": "US",
    "boston": "US",
    "london": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "uk": "GB",
    "united kingdom": "GB",
    "ireland": "IE",
    "dublin": "IE",
    "paris": "FR",
    "france": "FR",
    "berlin": "DE",
    "germany": "DE",
    "amsterdam": "NL",
    "netherlands": "NL",
    "madrid": "ES",
    "spain": "ES",
    "rome": "IT",
    "italy": "IT",
    "stockholm": "SE",
    "sweden": "SE",
    "oslo": "NO",
    "norway": "NO",
    "copenhagen": "DK",
    "denmark": "DK",
    "helsinki": "FI",
    "finland": "FI",
    "warsaw": "PL",
    "poland": "PL",
    "prague": "CZ",
    "czech": "CZ",
    "vienna": "AT",
    "austria": "AT",
    "zurich": "CH",
    "switzerland": "CH",
    "brussels": "BE",
    "belgium": "BE",
    "lisbon": "PT",
    "portugal": "PT",
    "tokyo": "JP",
    "japan": "JP",
    "seoul": "KR",
    "south korea": "KR",
    "korea": "KR",
    "beijing": "CN",
    "shanghai": "CN",
    "china": "CN",
    "hong kong": "HK",
    "taiwan": "TW",
    "singapore": "SG",
    "sydney": "AU",
    "melbourne": "AU",
    "australia": "AU",
    "toronto": "CA",
    "vancouver": "CA",
    "canada": "CA",
    "mexico": "MX",
    "brazil": "BR",
    "argentina": "AR",
    "chile": "CL",
    "india": "IN",
    "bangalore": "IN",
    "bengaluru": "IN",
    "delhi": "IN",
    "mumbai": "IN",
    "israel": "IL",
    "tel aviv": "IL",
    "uae": "AE",
    "dubai": "AE",
    "saudi": "SA",
    "egypt": "EG",
    "nigeria": "NG",
    "south africa": "ZA",
    "russia": "RU",
    "moscow": "RU",
}


def clean_company(company):
    if not company:
        return ""
    value = company.strip().lower()
    if value.startswith("@"):
        value = value[1:]
    value = COMPANY_SUFFIX_RE.sub("", value)
    value = NON_WORD_RE.sub(" ", value)
    value = " ".join(value.split())
    return value


def _lookup_country(raw):
    if not raw:
        return None
    value = raw.strip().lower()
    if not value:
        return None
    if value in COMMON_LOCATION_MAP:
        return COMMON_LOCATION_MAP[value]

    try:
        country = pycountry.countries.lookup(raw)
        if country:
            return country.alpha_2
    except LookupError:
        return None
    return None


def normalize_location_to_country(location):
    if not location:
        return None
    cleaned = location.strip().lower()
    if not cleaned:
        return None
    if cleaned in COMMON_LOCATION_MAP:
        return COMMON_LOCATION_MAP[cleaned]
    parts = [part.strip() for part in re.split(r"[,/|]", cleaned) if part.strip()]
    for part in reversed(parts):
        match = _lookup_country(part)
        if match:
            return match
        if part in COMMON_LOCATION_MAP:
            return COMMON_LOCATION_MAP[part]
    return None


def load_stargazers(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return data
    return data.get("stargazers", [])


def enrich_and_aggregate(input_path, output_path):
    stargazers = load_stargazers(input_path)
    country_counts = {}
    company_counts = {}
    for user in stargazers:
        country = normalize_location_to_country(user.get("location", ""))
        if country:
            country_counts[country] = country_counts.get(country, 0) + 1
        company = clean_company(user.get("company", ""))
        if company:
            company_counts[company] = company_counts.get(company, 0) + 1
    payload = {
        "country_counts": country_counts,
        "company_counts": company_counts,
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)
    return country_counts, company_counts
