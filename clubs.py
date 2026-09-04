# -*- coding: utf-8 -*-
"""
clubs.py — the canonical club registry.

One entry per real-world club, keyed by a short stable ID. Season fixtures in
seasons.py reference these keys, so a club is defined exactly once no matter how
many seasons it appears in. This is what makes the Clubs table a true canonical
registry rather than a pile of duplicates.

Where a club competed under a different name in this era, the modern/most
recognisable name is used as canonical and the period name is recorded in
`notes`. (A period-accurate club-name display is a planned enhancement — see
ROADMAP.md — mirroring how competition lineage already preserves period names.)

Country codes follow the abbreviations RSSSF uses for the period (e.g. FRG/GDR
for West/East Germany, TCH for Czechoslovakia, SAA for the Saar, YUG, etc.).
"""

CLUBS = {
    # --- 1955-56 -------------------------------------------------------------
    "real_madrid":   {"name": "Real Madrid",          "country": "ESP", "city": "Madrid"},
    "servette":      {"name": "Servette FC",          "country": "SUI", "city": "Geneva"},
    "sporting_cp":   {"name": "Sporting CP",          "country": "POR", "city": "Lisbon"},
    "partizan":      {"name": "FK Partizan",          "country": "YUG", "city": "Belgrade"},
    "rapid_wien":    {"name": "SK Rapid Wien",        "country": "AUT", "city": "Vienna",
                      "notes": "Listed by RSSSF as SK Rapid Vienna in some seasons."},
    "psv":           {"name": "PSV Eindhoven",        "country": "NED", "city": "Eindhoven"},
    "milan":         {"name": "Milan",                "country": "ITA", "city": "Milan",
                      "notes": "Listed by RSSSF as Milan AC / AC Milan."},
    "saarbrucken":   {"name": "1. FC Saarbrücken",    "country": "SAA", "city": "Saarbrücken",
                      "notes": "Represented the then-separate Saar association."},
    "rw_essen":      {"name": "Rot-Weiss Essen",      "country": "FRG", "city": "Essen"},
    "hibernian":     {"name": "Hibernian",            "country": "SCO", "city": "Edinburgh"},
    "djurgarden":    {"name": "Djurgårdens IF",       "country": "SWE", "city": "Stockholm"},
    "gwardia":       {"name": "Gwardia Warszawa",     "country": "POL", "city": "Warsaw"},
    "mtk":           {"name": "MTK Budapest",         "country": "HUN", "city": "Budapest",
                      "notes": "Competed as Vörös Lobogó in 1955-56."},
    "anderlecht":    {"name": "RSC Anderlecht",       "country": "BEL", "city": "Brussels"},
    "agf":           {"name": "AGF Aarhus",           "country": "DEN", "city": "Aarhus"},
    "reims":         {"name": "Stade de Reims",       "country": "FRA", "city": "Reims"},

    # --- added 1956-57 -------------------------------------------------------
    "nice":          {"name": "OGC Nice",             "country": "FRA", "city": "Nice"},
    "porto":         {"name": "FC Porto",             "country": "POR", "city": "Porto"},
    "bilbao":        {"name": "Athletic Bilbao",      "country": "ESP", "city": "Bilbao"},
    "man_utd":       {"name": "Manchester United",    "country": "ENG", "city": "Manchester"},
    "dortmund":      {"name": "Borussia Dortmund",    "country": "FRG", "city": "Dortmund"},
    "spora":         {"name": "CA Spora Luxembourg",  "country": "LUX", "city": "Luxembourg City"},
    "dinamo_buc":    {"name": "Dinamo București",     "country": "ROM", "city": "Bucharest"},
    "galatasaray":   {"name": "Galatasaray",          "country": "TUR", "city": "Istanbul"},
    "slovan":        {"name": "Slovan Bratislava",    "country": "TCH", "city": "Bratislava",
                      "notes": "Competed as ČH (Červená hviezda) Bratislava in this era."},
    "cwks_warsaw":   {"name": "CWKS Warsaw",          "country": "POL", "city": "Warsaw",
                      "notes": "Later renamed Legia Warsaw."},
    "rangers":       {"name": "Rangers",              "country": "SCO", "city": "Glasgow"},
    "honved":        {"name": "Budapest Honvéd",      "country": "HUN", "city": "Budapest"},
    "rapid_jc":      {"name": "Rapid JC Heerlen",     "country": "NED", "city": "Heerlen",
                      "notes": "Later merged into Roda JC."},
    "red_star":      {"name": "Red Star Belgrade",    "country": "YUG", "city": "Belgrade",
                      "notes": "Crvena zvezda."},
    "cdna_sofia":    {"name": "CDNA Sofia",           "country": "BUL", "city": "Sofia",
                      "notes": "Army club; later CSKA Sofia."},
    "grasshopper":   {"name": "Grasshopper-Club Zürich", "country": "SUI", "city": "Zürich"},
    "fiorentina":    {"name": "Fiorentina",           "country": "ITA", "city": "Florence"},
    "ifk_norr":      {"name": "IFK Norrköping",       "country": "SWE", "city": "Norrköping"},

    # --- added 1957-58 -------------------------------------------------------
    "sevilla":       {"name": "Sevilla CF",           "country": "ESP", "city": "Seville"},
    "benfica":       {"name": "SL Benfica",           "country": "POR", "city": "Lisbon"},
    "glenavon":      {"name": "Glenavon",             "country": "NIR", "city": "Lurgan"},
    "vasas":         {"name": "Vasas SC",             "country": "HUN", "city": "Budapest"},
    "wismut":        {"name": "Wismut Karl-Marx-Stadt", "country": "GDR", "city": "Karl-Marx-Stadt",
                      "notes": "Now Chemnitzer FC."},
    "shamrock":      {"name": "Shamrock Rovers",      "country": "IRL", "city": "Dublin"},
    "dudelange":     {"name": "Stade Dudelange",      "country": "LUX", "city": "Dudelange"},
    "st_etienne":    {"name": "AS Saint-Étienne",     "country": "FRA", "city": "Saint-Étienne"},
    "antwerp":       {"name": "Royal Antwerp",        "country": "BEL", "city": "Antwerp",
                      "notes": "Listed by RSSSF as RFC Antwerp."},
    "ajax":          {"name": "Ajax",                 "country": "NED", "city": "Amsterdam"},
    "young_boys":    {"name": "BSC Young Boys",       "country": "SUI", "city": "Bern"},
    "dukla":         {"name": "Dukla Prague",         "country": "TCH", "city": "Prague",
                      "notes": "Listed by RSSSF as Dukla Praha in some seasons."},
    "cca_buc":       {"name": "CCA București",        "country": "ROM", "city": "Bucharest",
                      "notes": "Army club; later Steaua București / FCSB."},

    # --- added 1958-59 -------------------------------------------------------
    "juventus":      {"name": "Juventus",             "country": "ITA", "city": "Turin"},
    "wiener_sc":     {"name": "Wiener Sport-Club",    "country": "AUT", "city": "Vienna"},
    "dinamo_zagreb": {"name": "Dinamo Zagreb",        "country": "YUG", "city": "Zagreb"},
    "kb_copenhagen": {"name": "KB Copenhagen",        "country": "DEN", "city": "Copenhagen",
                      "notes": "Later merged into FC København."},
    "schalke":       {"name": "FC Schalke 04",        "country": "FRG", "city": "Gelsenkirchen"},
    "atletico":      {"name": "Atlético Madrid",      "country": "ESP", "city": "Madrid"},
    "drumcondra":    {"name": "Drumcondra",           "country": "IRL", "city": "Dublin"},
    "petrolul":      {"name": "Petrolul Ploiești",    "country": "ROM", "city": "Ploiești"},
    "jeunesse":      {"name": "Jeunesse Esch",        "country": "LUX", "city": "Esch-sur-Alzette"},
    "ifk_gbg":       {"name": "IFK Gothenburg",       "country": "SWE", "city": "Gothenburg"},
    "polonia":       {"name": "Polonia Bytom",        "country": "POL", "city": "Bytom"},
    "dos_utrecht":   {"name": "DOS Utrecht",          "country": "NED", "city": "Utrecht",
                      "notes": "Later merged into FC Utrecht."},
    "standard":      {"name": "Standard Liège",       "country": "BEL", "city": "Liège"},
    "hearts":        {"name": "Heart of Midlothian",  "country": "SCO", "city": "Edinburgh"},
    "ards":          {"name": "Ards",                 "country": "NIR", "city": "Newtownards"},
    "besiktas":      {"name": "Beşiktaş",             "country": "TUR", "city": "Istanbul"},
    "olympiakos":    {"name": "Olympiakos",           "country": "GRE", "city": "Piraeus"},
    "wolves":        {"name": "Wolverhampton Wanderers", "country": "ENG", "city": "Wolverhampton"},
    "hps_helsinki":  {"name": "HPS Helsinki",         "country": "FIN", "city": "Helsinki"},

    # --- added 1959-60 -------------------------------------------------------
    "lks_lodz":      {"name": "ŁKS Łódź",             "country": "POL", "city": "Łódź"},
    "fenerbahce":    {"name": "Fenerbahçe",           "country": "TUR", "city": "Istanbul"},
    "csepel":        {"name": "Csepel SC",            "country": "HUN", "city": "Budapest"},
    "vorwarts":      {"name": "ASK Vorwärts Berlin",  "country": "GDR", "city": "Berlin",
                      "notes": "Army club; later Vorwärts Frankfurt (Oder)."},
    "barcelona":     {"name": "FC Barcelona",         "country": "ESP", "city": "Barcelona"},
    "linfield":      {"name": "Linfield",             "country": "NIR", "city": "Belfast"},
    "eintracht":     {"name": "Eintracht Frankfurt",  "country": "FRG", "city": "Frankfurt"},
    "sparta_rot":    {"name": "Sparta Rotterdam",     "country": "NED", "city": "Rotterdam"},
    "b1909_odense":  {"name": "B1909 Odense",         "country": "DEN", "city": "Odense"},
    "kups":          {"name": "KuPS Kuopio",          "country": "FIN", "city": "Kuopio"},

    # --- added 1960-61 European Cup -----------------------------------------
    "ujpest":        {"name": "Újpesti Dózsa",        "country": "HUN", "city": "Budapest",
                      "notes": "Later Újpest FC."},
    "fredrikstad":   {"name": "Fredrikstad FK",       "country": "NOR", "city": "Fredrikstad"},
    "hifk":          {"name": "HIFK Helsinki",        "country": "FIN", "city": "Helsinki",
                      "notes": "Listed by RSSSF as HIFK / IFK Helsingfors."},
    "ifk_malmo":     {"name": "IFK Malmö",            "country": "SWE", "city": "Malmö"},
    "limerick":      {"name": "Limerick",             "country": "IRL", "city": "Limerick"},
    "lierse":        {"name": "Lierse SK",            "country": "BEL", "city": "Lier"},
    "hradec":        {"name": "Spartak Hradec Králové", "country": "TCH", "city": "Hradec Králové"},
    "hamburg":       {"name": "Hamburger SV",         "country": "FRG", "city": "Hamburg"},
    "burnley":       {"name": "Burnley",              "country": "ENG", "city": "Burnley"},
    "panathinaikos": {"name": "Panathinaikos",        "country": "GRE", "city": "Athens"},

    # --- added 1960-61 Cup Winners' Cup -------------------------------------
    "red_star_brno": {"name": "Rudá Hvězda Brno",     "country": "TCH", "city": "Brno",
                      "notes": "Red Star Brno; later Zbrojovka Brno."},
    "ferencvaros":   {"name": "Ferencváros",          "country": "HUN", "city": "Budapest"},
    "lucerne":       {"name": "FC Luzern",            "country": "SUI", "city": "Lucerne",
                      "notes": "Listed by RSSSF as FC Lucerne."},
    "austria_wien":  {"name": "FK Austria Wien",      "country": "AUT", "city": "Vienna"},
    "gladbach":      {"name": "Borussia Mönchengladbach", "country": "FRG", "city": "Mönchengladbach"},

    # --- added 1961-62 European Cup -----------------------------------------
    "nurnberg":      {"name": "1. FC Nürnberg",       "country": "FRG", "city": "Nuremberg"},
    "hibernians_malta": {"name": "Hibernians",        "country": "MLT", "city": "Paola",
                      "notes": "Paola, Malta; distinct from Hibernian (Edinburgh)."},
    "feyenoord":     {"name": "Feyenoord",            "country": "NED", "city": "Rotterdam",
                      "notes": "Spelt Feijenoord in this era; RSSSF uses Feĳenoord."},
    "gornik":        {"name": "Górnik Zabrze",        "country": "POL", "city": "Zabrze"},
    "tottenham":     {"name": "Tottenham Hotspur",    "country": "ENG", "city": "London"},
    "monaco":        {"name": "AS Monaco",            "country": "FRA", "city": "Monaco"},
    "b1913":         {"name": "B1913 Odense",         "country": "DEN", "city": "Odense"},
    "haka":          {"name": "Haka Valkeakoski",     "country": "FIN", "city": "Valkeakoski",
                      "notes": "Listed by RSSSF as Valkeakosken Haka."},
}


# Period-accurate display names. Build populates club_name_history from these.
# Keys reference CLUBS; season_label is matched to edition rows at build time.
CLUB_NAME_HISTORY = [
    {
        "club": "mtk",
        "season_label": "1955-56",
        "name_used": "Vörös Lobogó",
        "notes": "Official name during the inaugural European Cup.",
    },
    {
        "club": "slovan",
        "season_label": "1956-57",
        "name_used": "CH Bratislava",
        "notes": "Červená hviezda (Red Star) Bratislava.",
    },
    {
        "club": "slovan",
        "season_label": "1959-60",
        "name_used": "CH Bratislava",
        "notes": "Červená hviezda (Red Star) Bratislava.",
    },
    {
        "club": "cwks_warsaw",
        "season_label": "1960-61",
        "name_used": "Legia Warsaw",
        "notes": "Competed as Legia Warsaw in the European Cup.",
    },
    {
        "club": "cca_buc",
        "season_label": "1957-58",
        "name_used": "CCA București",
        "notes": "Army club; later Steaua București / FCSB.",
    },
    {
        "club": "wismut",
        "season_label": "1957-58",
        "name_used": "Wismut Karl-Marx-Stadt",
        "notes": "Now Chemnitzer FC.",
    },
    {
        "club": "wismut",
        "season_label": "1960-61",
        "name_used": "Wismut Karl-Marx-Stadt",
        "notes": "Now Chemnitzer FC.",
    },
    {
        "club": "feyenoord",
        "season_label": "1961-62",
        "name_used": "Feijenoord",
        "notes": "Dutch spelling in use until the 1970s; RSSSF prints Feĳenoord.",
    },
    {
        "club": "haka",
        "season_label": "1961-62",
        "name_used": "Valkeakosken Haka",
        "notes": "Period name as listed by RSSSF.",
    },
]
