// Escudos de clubes: id de crests.football-data.org por nombre (sin tildes, en minúsculas). Varios alias por club.
window.ESCUDOS = (() => {
  const C = {
    // LaLiga
    77: ["athletic", "athletic club", "athletic bilbao", "athletic de bilbao"], 78: ["atletico", "atletico de madrid", "atletico madrid", "atleti"],
    79: ["osasuna", "ca osasuna"], 80: ["espanyol", "rcd espanyol"], 81: ["barcelona", "fc barcelona", "barca"], 82: ["getafe"],
    86: ["real madrid"], 87: ["rayo", "rayo vallecano"], 88: ["levante"], 89: ["mallorca", "rcd mallorca"], 90: ["betis", "real betis"],
    92: ["real sociedad"], 94: ["villarreal"], 95: ["valencia"], 263: ["alaves", "deportivo alaves"], 275: ["las palmas", "ud las palmas"],
    298: ["girona"], 558: ["celta", "celta de vigo", "rc celta"], 559: ["sevilla", "sevilla fc"], 745: ["leganes"], 250: ["valladolid", "real valladolid"],
    285: ["elche"], 1048: ["oviedo", "real oviedo"],
    // Premier League
    57: ["arsenal"], 58: ["aston villa"], 61: ["chelsea"], 62: ["everton"], 63: ["fulham"], 64: ["liverpool"], 65: ["manchester city", "man city"],
    66: ["manchester united", "man united", "manchester utd"], 67: ["newcastle", "newcastle united"], 73: ["tottenham", "tottenham hotspur", "spurs"],
    76: ["wolves", "wolverhampton"], 328: ["burnley"], 341: ["leeds", "leeds united"], 351: ["nottingham forest", "nottingham", "forest"],
    354: ["crystal palace"], 397: ["brighton"], 402: ["brentford"], 563: ["west ham", "west ham united"], 1044: ["bournemouth"], 71: ["sunderland"],
    338: ["leicester"], 340: ["southampton"], 349: ["ipswich"],
    // Serie A
    98: ["milan", "ac milan"], 99: ["fiorentina"], 100: ["roma", "as roma"], 102: ["atalanta"], 103: ["bolonia", "bologna"], 104: ["cagliari"],
    107: ["genoa"], 108: ["inter", "inter de milan", "internazionale"], 109: ["juventus"], 110: ["lazio"], 112: ["parma"], 113: ["napoles", "napoli"],
    115: ["udinese"], 450: ["verona", "hellas verona"], 586: ["torino"], 5890: ["lecce"], 7397: ["como"], 445: ["empoli"], 471: ["sassuolo"],
    487: ["pisa"], 457: ["cremonese"],
    // Bundesliga
    1: ["colonia", "koln", "fc koln"], 2: ["hoffenheim"], 3: ["leverkusen", "bayer leverkusen"], 4: ["dortmund", "borussia dortmund"],
    5: ["bayern", "bayern munich", "bayern de munich"], 7: ["hamburgo", "hamburger sv", "hamburgo sv"], 10: ["stuttgart"], 11: ["wolfsburgo", "wolfsburg"],
    12: ["werder bremen", "werder"], 15: ["maguncia", "mainz"], 16: ["augsburgo", "augsburg"], 17: ["friburgo", "freiburg"],
    18: ["borussia monchengladbach", "monchengladbach", "gladbach"], 19: ["eintracht frankfurt", "eintracht", "frankfurt"], 20: ["st. pauli", "st pauli"],
    28: ["union berlin"], 44: ["heidenheim"], 721: ["leipzig", "rb leipzig"],
    // Ligue 1
    511: ["toulouse", "toulouse fc"], 512: ["brest"], 516: ["marsella", "marseille", "olympique de marsella"], 521: ["lille"], 522: ["niza", "nice"],
    523: ["lyon", "olympique de lyon"], 524: ["psg", "paris saint-germain", "paris saint germain", "paris sg"], 525: ["lorient"], 529: ["rennes"],
    532: ["angers"], 533: ["le havre"], 543: ["nantes"], 545: ["metz"], 546: ["lens"], 548: ["monaco"], 576: ["estrasburgo", "strasbourg"],
    1045: ["paris fc"], 519: ["auxerre"],
    // Europa (los que más salen en Champions/Europa League)
    498: ["sporting", "sporting de portugal", "sporting cp"], 503: ["oporto", "porto", "fc porto"], 1903: ["benfica"], 678: ["ajax"], 674: ["psv", "psv eindhoven"],
    675: ["feyenoord"], 732: ["celtic"], 851: ["brujas", "club brugge"], 610: ["galatasaray"],
  };
  const m = {};
  for (const [id, nombres] of Object.entries(C)) for (const n of nombres) m[n] = id;
  return m;
})();
