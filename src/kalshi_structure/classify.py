"""Deterministic classification of Elections + Politics series.

Most of the taxonomy is recoverable from metadata that Kalshi already publishes —
ticker grammar, `settlement_sources`, contract template, close dates — so it is derived
by rule here rather than guessed by a language model. Rules are reproducible, auditable
and survive a re-fetch; a one-off labelling pass is none of those things.

Everything this module cannot determine is labelled ``unknown`` rather than filled with
a plausible value, and :func:`coverage` reports how much of the universe that is. The
residue is the honest input to any manual or model-assisted pass.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

# --- controlled vocabularies -------------------------------------------------------

DOMAINS = (
    "us_federal_legislative_election", "us_federal_executive_election",
    "us_state_election", "us_local_election", "us_primary", "foreign_election",
    "legislation", "executive_action", "personnel", "judicial", "geopolitics",
    "party_internal", "scandal_legal", "civic_statistic", "speculative_longshot",
    "unknown",
)
SUBJECT_TYPES = (
    "party_control", "candidate_identity", "vote_margin", "vote_share", "turnout",
    "seat_count", "placement", "office_tenure", "event_occurrence", "count_threshold",
    "date_of_event", "price_or_amount", "unknown",
)
AUTHORITIES = (
    "state_election_authority", "us_congress", "federal_agency", "court",
    "media_consensus", "party_organisation", "company_or_org", "market_data",
    "foreign_government", "white_house", "unknown",
)

STATES = (
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT "
    "NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC"
).split()
_STATE_SET = frozenset(STATES)

# --- settlement authority ----------------------------------------------------------

_AUTHORITY_RULES = (
    ("state_election_authority", re.compile(r"state government|secretary of state|election authority|board of elections|canvass", re.I)),
    ("us_congress", re.compile(r"library of congress|united states congress|u\.?s\.? (senate|house)|house of representatives|congress\.gov|clerk of the house", re.I)),
    ("court", re.compile(r"supreme court|court of appeals|\bcourt\b|judiciary", re.I)),
    ("white_house", re.compile(r"white house|office of the presidency|executive office", re.I)),
    ("party_organisation", re.compile(r"democratic party|republican party|national committee|\bdnc\b|\brnc\b", re.I)),
    ("federal_agency", re.compile(r"bureau of labor|census|federal reserve|department of|\bfec\b|\bcbo\b|\bgao\b|treasury|\bfda\b|\bcdc\b", re.I)),
    ("foreign_government", re.compile(r"tribunal superior eleitoral|electoral commission|parliament|ministry|european|\beu\b|united nations", re.I)),
    ("market_data", re.compile(r"portwatch|bloomberg|refinitiv|exchange|yahoo finance|\baaa\b", re.I)),
    ("media_consensus", re.compile(r"new york times|associated press|reuters|politico|axios|washington post|fox news|wall street journal|guardian|\bcnn\b|\babc\b|\bnbc\b|\bcbs\b|semafor", re.I)),
)


def settlement_authority(sources: str | None) -> str:
    """Map the named settlement sources onto a controlled authority class.

    Order matters: a contract citing both a state canvass and a wire service is resolved
    by the canvass, with media only accelerating it, so the more specific authority wins.
    """
    text = sources or ""
    if not text.strip():
        return "unknown"
    for label, rx in _AUTHORITY_RULES:
        if rx.search(text):
            return label
    return "unknown"


# --- ticker grammar ----------------------------------------------------------------

_RE_HOUSE_DISTRICT = re.compile(r"^(?:KX)?HOUSE(?:RACE-)?([A-Z]{2})(\d{2})\b")
_RE_STATE_OFFICE = re.compile(r"^(?:KX)?(SENATE|GOVPARTY|GOV|STATELEG)([A-Z]{2})\b")
_RE_STATE_PRIMARY = re.compile(r"^KX([A-Z]{2})PRIMARY\b")
# Some House races are written KX<ST><DISTRICT><SUFFIX> instead of KXHOUSERACE-<ST><DD>
_RE_DISTRICT_ALT = re.compile(r"^KX([A-Z]{2})(\d{1,2})(PERSON|WINNER|SWINNER|SPECIAL|ELECTION)")

_DERIVATIVE_FAMILIES = {
    "KXMIDTERMMOV": "vote_margin",
    "KXPRIMARYMOV": "vote_margin",
    "KXLAMOV": "vote_margin",
    "KXPRIMARYMOV2": "vote_margin",
    "KXMIDTERMVOTETURN": "turnout",
    "KXVOTEPRIMARY": "vote_share",
    "KXPRIMARYPLACE": "placement",
    "KXPRIMARYVOTE": "vote_share",
}

# Countries and foreign polities that appear in this universe, used both to route a
# series to a foreign domain and to fill geography.
FOREIGN = {
    "IRAN": "Iran", "VENEZUELA": "Venezuela", "BRAZIL": "Brazil", "BR": "Brazil",
    "UKRAINE": "Ukraine", "RUSSIA": "Russia", "CHINA": "China", "TAIWAN": "Taiwan",
    "ISRAEL": "Israel", "GAZA": "Gaza", "GREENLAND": "Greenland", "CANADA": "Canada",
    "MEXICO": "Mexico", "FRENCH": "France", "FRANCE": "France", "GERMAN": "Germany",
    "UK": "United Kingdom", "CLACTON": "United Kingdom", "JAPAN": "Japan",
    "INDIA": "India", "KOREA": "Korea", "CUBA": "Cuba", "PANAMA": "Panama",
    "ARGENTINA": "Argentina", "NIGERIA": "Nigeria", "PHILIPPINES": "Philippines",
    "SYRIA": "Syria", "YEMEN": "Yemen", "LEBANON": "Lebanon", "TURKEY": "Turkey",
    "POLAND": "Poland", "ITALY": "Italy", "SPAIN": "Spain", "AUSTRALIA": "Australia",
    "PUTIN": "Russia", "ZELENSKY": "Ukraine", "MADURO": "Venezuela",
    "PAHLAVI": "Iran", "NETANYAHU": "Israel", "DIAZ": "Cuba",
}
_RE_FOREIGN = re.compile(r"|".join(sorted(FOREIGN, key=len, reverse=True)), re.I)

_DOMAIN_RULES = (
    # Ordered by specificity: an earlier rule wins, so narrow patterns come first.
    ("us_primary", re.compile(r"PRIMARY|NOMINEE|NOM[RD]?\b|CAUCUS|\bRUN\b|DRUN|RRUN|DECLAREPRES", re.I)),
    ("us_federal_executive_election", re.compile(r"^KX(PRES|VPRES|DPRESPRIMARY|RPRESPRIMARY|ELECTORAL|POWER)|^POWER|ELECTORALCOLLEGE", re.I)),
    ("us_federal_legislative_election", re.compile(
        r"^(KX)?(HOUSE|SENATE|CONTROL[HS]|MIDTERM|BALANCEPOWER|BLUEWAVE|BLUETSUNAMI|REDWAVE)"
        r"|SENATESEATS|HOUSESEATS|SENATE(?:PERSON|MID)|CLOSESTSENATE|METXCOMBO|SENGOVCOMBO"
        r"|HOUSEDEM|HOUSEREP|WINSTATE|REDISTRICT", re.I)),
    ("us_federal_legislative_election", _RE_DISTRICT_ALT),
    ("us_state_election", re.compile(r"^(KX)?(GOVPARTY|GOV|STATELEG|ATTORNEYGEN|SECSTATE)|GOVERNOR", re.I)),
    ("us_local_election", re.compile(r"MAYOR|CITYCOUNCIL|^KXNYC|^KXLA(?!MOV)", re.I)),
    ("judicial", re.compile(r"SCOTUS|JUDGE|JUSTICE|COURT|IMPEACHJUDGE|ALITO|THOMAS|SOTOMAYOR|JUDICIARY|FISA", re.I)),
    ("scandal_legal", re.compile(r"IMPEACH|INDICT|CONVICT|EPSTEIN|SCANDAL|ARREST|SUBPOENA|FEDERALCHARGE|PARDON", re.I)),
    # Departure/tenure questions: OUT, LEAVE, RESIGN, RETIRE anywhere in the ticker.
    ("personnel", re.compile(
        r"NEXTAG|ADMINLEAVE|CABINET|CHAIR|SPEAKER|NEXTDNC|NEXTRNC|APPOINT|CONFIRM"
        r"|OUT\b|OUT\d|[A-Z]OUT|LEAVE|RESIGN|RETIRE|DEPARTURE|LEADERSOUT|AGENCYELIM", re.I)),
    ("executive_action", re.compile(
        r"EXECORDER|TARIFF|DEPORT|SHUTDOWN|EMERGENCY|TROOPS|STRIKE|VISIT|MEETING"
        r"|TRUMPCOUNTRIES|BTCRESERVE|CANAL|SUSPENDGASTAX|MJSCHEDULE|RESCHEDUL", re.I)),
    ("legislation", re.compile(
        r"BILL|ACT\b|REPEAL|AMEND|LEGISLA|FUNDING|DEBTCEIL|BUDGET|SAVEACT|GAMBLINGREPEAL"
        r"|DOED|EXTEND|LIMIT|CAP\b|ACAEXT|CCLIMIT|REAUTH|BAN\b|TRDBAN|TAX|WAIVE"
        r"|FEDEND|ABOLISH|ELIMINAT|MANDATE|SUBSIDY|TARIFFEXEMPT", re.I)),
    ("foreign_election", re.compile(
        r"^(BR|UK|FR|DE|CA|MX|JP|IN|AU)(PRES|PM|ELECT|PARTY)|WORLDLEADER|NEXTPM"
        r"|NEXTIRANLEADER|PAHLAVI|BYELECTION|ELECTVENEZUELA|VENEZUELALEADER"
        r"|FRENCHPRES|UKPARTY|BRPRES", re.I)),
    ("geopolitics", re.compile(
        r"IRAN|GREENLAND|UKRAINE|RUSSIA|CHINA|TAIWAN|ISRAEL|GAZA|NATO|BRICS|HORMUZ"
        r"|TERRITORY|EXPAND|CEASEFIRE|TREATY|EU(EXIT|EXPANSION)|STATE51|ZELENSKY|PUTIN"
        r"|NOBELPEACE|POPEVISIT|NETANYAHU", re.I)),
    ("party_internal", re.compile(r"ENDORSE|PARTYSWITCH|CAUCUSWITH|THIRDPARTY|BALLOTAMERICA|DNC|RNC", re.I)),
    ("civic_statistic", re.compile(r"POPCHANGE|CENSUS|BILLIONAIRES|SUBWAY|GASM|APPROVAL|POLL|COMBO", re.I)),
)


def _geography(series_ticker: str, title: str, domain: str = "unknown") -> str:
    m = _RE_HOUSE_DISTRICT.match(series_ticker)
    if m and m.group(1) in _STATE_SET:
        return f"US-{m.group(1)}{m.group(2)}"
    m = _RE_STATE_OFFICE.match(series_ticker)
    if m and m.group(2) in _STATE_SET:
        return f"US-{m.group(2)}"
    m = _RE_STATE_PRIMARY.match(series_ticker)
    if m and m.group(1) in _STATE_SET:
        return f"US-{m.group(1)}"
    m = _RE_DISTRICT_ALT.match(series_ticker)
    if m and m.group(1) in _STATE_SET:
        return f"US-{m.group(1)}{int(m.group(2)):02d}"
    # Title is a weaker signal than the ticker and is only consulted as a fallback,
    # because titles are sometimes plain wrong (SENATELA-26 is titled "Kentucky
    # Senate winner?" and settles on Kentucky).
    for st in STATES:
        if re.search(rf"\b{st}-\d{{1,2}}\b", title or ""):
            return f"US-{st}"
    m = _RE_FOREIGN.search(series_ticker) or _RE_FOREIGN.search(title or "")
    if m:
        return FOREIGN.get(m.group(0).upper(), "international")
    if domain in ("foreign_election", "geopolitics"):
        return "international"
    if domain in ("us_federal_legislative_election", "us_federal_executive_election",
                  "legislation", "executive_action", "judicial", "personnel",
                  "party_internal", "scandal_legal", "us_primary"):
        return "US-national"
    return "unknown"


def _subject_type(series_ticker: str, template: str, title: str) -> str:
    for fam, subject in _DERIVATIVE_FAMILIES.items():
        if series_ticker.startswith(fam):
            return subject
    t = f"{series_ticker} {title or ''}"
    if re.search(r"SEATS|HOWMANY|COUNT\b|NUMBER OF", t, re.I):
        return "seat_count"
    if re.search(r"CONTROL|PARTY WIN|which party", t, re.I):
        return "party_control"
    if re.search(r"TURNOUT", t, re.I):
        return "turnout"
    if re.search(r"MARGIN", t, re.I):
        return "vote_margin"
    if re.search(r"VOTE SHARE|PERCENT OF THE VOTE", t, re.I):
        return "vote_share"
    if re.search(r"OUT-|RESIGN|LEAVE|TENURE|REMAIN AS|STILL BE", t, re.I):
        return "office_tenure"
    if template == "deadline":
        return "date_of_event"
    if template == "threshold":
        return "count_threshold"
    if template == "bucket":
        return "price_or_amount"
    if template == "entity_menu":
        return "candidate_identity"
    if template == "binary":
        return "event_occurrence"
    return "unknown"


def _cycle(series_ticker: str, latest_close: str, title: str) -> str:
    t = f"{series_ticker} {title or ''}"
    if re.search(r"MIDTERM|CONTROL[HS]-2026|-26\b", t) or "2026" in t:
        cyc = "2026-midterm"
    elif re.search(r"PRES.*-?28|2028", t):
        cyc = "2028-presidential"
    elif re.search(r"TRUMP|-29\b|2029", t):
        cyc = "trump-term-2"
    else:
        cyc = "unknown"
    if cyc == "unknown" and latest_close[:4].isdigit():
        cyc = f"closes-{latest_close[:4]}"
    return cyc


def _time_class(frequency: str, template: str) -> str:
    if frequency in ("daily", "hourly", "weekly", "fifteen_min"):
        return "data_release"
    if template == "deadline":
        return "deadline_race"
    if frequency in ("one_off", "custom", "annual", "quarterly", "monthly"):
        return "scheduled_event"
    return "unknown"


@dataclass(frozen=True)
class Classification:
    series_ticker: str
    domain: str
    subject_type: str
    geography: str
    cycle: str
    resolution_authority: str
    time_class: str
    derivative_family: str
    is_derivative: bool


def classify_series(series_ticker: str, *, title: str = "", template: str = "",
                    settlement_sources: str = "", frequency: str = "",
                    latest_close: str = "") -> Classification:
    domain = "unknown"
    for label, rx in _DOMAIN_RULES:
        if rx.search(series_ticker) or rx.search(title or ""):
            domain = label
            break
    fam = next((f for f in _DERIVATIVE_FAMILIES if series_ticker.startswith(f)), "")
    return Classification(
        series_ticker=series_ticker,
        domain=domain,
        subject_type=_subject_type(series_ticker, template, title),
        geography=_geography(series_ticker, title, domain),
        cycle=_cycle(series_ticker, latest_close or "", title),
        resolution_authority=settlement_authority(settlement_sources),
        time_class=_time_class(frequency, template),
        derivative_family=fam,
        is_derivative=bool(fam),
    )


def coverage(rows: list[Classification]) -> dict:
    """Share of each field that is genuinely determined rather than defaulted."""
    n = len(rows) or 1
    fields = ("domain", "subject_type", "geography", "cycle",
              "resolution_authority", "time_class")
    return {f: round(sum(1 for r in rows if getattr(r, f) != "unknown") / n * 100, 1)
            for f in fields}


def as_dict(c: Classification) -> dict:
    return asdict(c)
