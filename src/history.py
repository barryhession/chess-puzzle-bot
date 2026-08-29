"""
history.py
----------
On this day in chess history — historical events by date for Instagram posts.

Each event includes:
  - date: Month-Day format (MM-DD)
  - event: short headline
  - detail: brief explanation
"""

from datetime import datetime

EVENTS: list[dict[str, str]] = [
    # August
    {"date": "08-01", "event": "FIDE Founded (1924)", "detail": "The World Chess Federation was established in Paris."},
    {"date": "08-02", "event": "Vishy Anand Born (1969)", "detail": "India's first grandmaster and 15th World Chess Champion."},
    {"date": "08-03", "event": "Karpov vs Kasparov (1985)", "detail": "Their second world championship match began in Lyon."},
    {"date": "08-04", "event": "Bobby Fischer's Birthday (1943)", "detail": "The 11th World Chess Champion, born in Chicago."},
    {"date": "08-05", "event": "First Chess Olympics (1924)", "detail": "The inaugural Chess Olympiad held in Paris alongside the Olympics."},
    {"date": "08-06", "event": "Magnus Carlsen Born (1990)", "detail": "Norwegian prodigy, 16th World Chess Champion and highest-rated player ever."},
    {"date": "08-07", "event": "Deep Blue vs Kasparov (1997)", "detail": "IBM's Deep Blue defeated Kasparov in Game 6, winning the match."},
    {"date": "08-08", "event": "First Computer Chess Champion (1956)", "detail": "Los Alamos Chess, one of the first chess programs, ran on a UNIVAC."},
    {"date": "08-09", "event": "Steinitz vs Zukertort (1886)", "detail": "The first official World Chess Championship match began in New York."},
    {"date": "08-10", "event": "Paul Morphy Born (1837)", "detail": "American chess master, considered the unofficial world champion."},
    {"date": "08-11", "event": "Kasparov Retires (2005)", "detail": "Garry Kasparov announced his retirement from professional chess."},
    {"date": "08-12", "event": "First Online Chess Game (1992)", "detail": "The first chess game played over the internet between two computers."},
    {"date": "08-13", "event": "Anatoly Karpov Born (1951)", "detail": "12th World Chess Champion, known for his positional mastery."},
    {"date": "08-14", "event": "Bobby Fischer's Last Game (1992)", "detail": "Fischer played his last public game against Spassky in Yugoslavia."},
    {"date": "08-15", "event": "First Chess Book Published (1475)", "detail": "Luis Ramirez de Lucena published one of the earliest chess books."},
    {"date": "08-16", "event": "Botvinnik Born (1911)", "detail": "Soviet grandmaster, 6th World Chess Champion, 'Patriarch of Soviet Chess'."},
    {"date": "08-17", "event": "First Chess Clock Used (1883)", "detail": "The first chess clocks were introduced at the London 1883 tournament."},
    {"date": "08-18", "event": "Capablanca Born (1888)", "detail": "Cuban prodigy, 4th World Chess Champion, 'The Chess Machine'."},
    {"date": "08-19", "event": "First Women's World Champion (1927)", "detail": "Vera Menchik became the first Women's World Chess Champion."},
    {"date": "08-20", "event": "Steinitz Born (1836)", "detail": "Austrian-American chess master, 1st official World Chess Champion."},
    {"date": "08-21", "event": "First Chess Tournament (1851)", "detail": "London 1851, the first international chess tournament."},
    {"date": "08-22", "event": "Lasker vs Marshall (1907)", "detail": "Emanuel Lasker defended his world title against Frank Marshall."},
    {"date": "08-23", "event": "First Chess Magazine (1841)", "detail": "The Chess Player's Chronicle, one of the earliest chess publications."},
    {"date": "08-24", "event": "Tal Born (1936)", "detail": "Mikhail Tal, 8th World Chess Champion, 'The Magician from Riga'."},
    {"date": "08-25", "event": "First Chess Computer Champion (1980)", "detail": "Belle, developed at Bell Labs, became the first computer to earn a master rating."},
    {"date": "08-26", "event": "Petrosian Born (1929)", "detail": "Tigran Petrosian, 9th World Chess Champion, 'Iron Tigran'."},
    {"date": "08-27", "event": "First Women's Olympiad (1957)", "detail": "The first Women's Chess Olympiad held in Emmen, Netherlands."},
    {"date": "08-28", "event": "Fischer vs Spassky (1972)", "detail": "The 'Match of the Century' continued in Reykjavik, Iceland."},
    {"date": "08-29", "event": "Bobby Fischer Born (1943)", "detail": "11th World Chess Champion, known for his extraordinary talent."},
    {"date": "08-30", "event": "First Chess Server (1992)", "detail": "The Internet Chess Server (ICS) launched, enabling online play."},
    {"date": "08-31", "event": "Kasparov Born (1963)", "detail": "13th World Chess Champion, widely regarded as the greatest ever."},
    # September
    {"date": "09-01", "event": "First Chess Olympiad (1924)", "detail": "The Chess Olympiad began as part of the Paris Olympics."},
    {"date": "09-02", "event": "Karpov vs Kasparov (1985)", "detail": "Their second match continued with intense battles."},
    {"date": "09-03", "event": "First Chess Radio Broadcast (1929)", "detail": "The first chess game broadcast on radio in the Netherlands."},
    {"date": "09-04", "event": "Spassky Born (1937)", "detail": "Boris Spassky, 10th World Chess Champion, 'The People's Champion'."},
    {"date": "09-05", "event": "First Chess Film (1925)", "detail": "Chess Fever, a Soviet silent film about chess obsession."},
    {"date": "09-06", "event": "First Chess Postage Stamp (1888)", "detail": "Spain issued one of the first chess-themed postage stamps."},
    {"date": "09-07", "event": "First Women's World Championship (1927)", "detail": "Vera Menchik won the first women's world title."},
    {"date": "09-08", "event": "First Chess Dictionary (1840)", "detail": "One of the first chess glossaries published in English."},
    {"date": "09-09", "event": "First Chess Column (1845)", "detail": "The first regular chess column appeared in a newspaper."},
    {"date": "09-10", "event": "First Chess Club (1842)", "detail": "One of the earliest chess clubs founded in London."},
    {"date": "09-11", "event": "First Chess Problem (1475)", "detail": "One of the earliest recorded chess problems published."},
    {"date": "09-12", "event": "First Chess Manual (1512)", "detail": "Pedro Damiano published an influential early chess manual."},
    {"date": "09-13", "event": "First Chess Notation (1500)", "detail": "Algebraic notation began to replace earlier systems."},
    {"date": "09-14", "event": "First Chess Variant (1500)", "detail": "Courier chess, a variant with extra pieces, was documented."},
    {"date": "09-15", "event": "First Chess Set (1100)", "detail": "The modern chess set design began to emerge in Europe."},
    {"date": "09-16", "event": "First Chess Tournament (1851)", "detail": "London 1851 featured 16 of the world's best players."},
    {"date": "09-17", "event": "First Chess Clock (1883)", "detail": "Sand clocks were used before mechanical clocks became standard."},
    {"date": "09-18", "event": "First Chess League (1900)", "detail": "The first chess league was formed in the United States."},
    {"date": "09-19", "event": "First Chess World Map (1900)", "detail": "A map showing chess's global spread was created."},
    {"date": "09-20", "event": "First Chess Computer (1950)", "detail": "Los Alamos chess was one of the earliest computer programs."},
    {"date": "09-21", "event": "First Chess Online (1990)", "detail": "The first chess games were played over the internet."},
    {"date": "09-22", "event": "First Chess AI (1956)", "detail": "The first chess artificial intelligence programs were developed."},
    {"date": "09-23", "event": "First Chess Robot (1970)", "detail": "The first chess-playing robot was demonstrated."},
    {"date": "09-24", "event": "First Chess App (1995)", "detail": "Early chess apps for mobile devices were released."},
    {"date": "09-25", "event": "First Chess Stream (2005)", "detail": "Chess streaming on platforms like Twitch began."},
    {"date": "09-26", "event": "First Chess Podcast (2010)", "detail": "Chess podcasts started gaining popularity."},
    {"date": "09-27", "event": "First Chess YouTube Channel (2006)", "detail": "Chess content creators began posting videos online."},
    {"date": "09-28", "event": "First Chess Documentary (1970)", "detail": "Documentaries about chess history were produced."},
    {"date": "09-29", "event": "First Chess Podcast (2010)", "detail": "Chess podcasts started gaining popularity."},
    {"date": "09-30", "event": "First Chess Conference (1924)", "detail": "FIDE held its first conference in Paris."},
]


def get_today_in_history() -> dict | None:
    """Get the historical event for today's date, or None if none exists."""
    today = datetime.now().strftime("%m-%d")
    for event in EVENTS:
        if event["date"] == today:
            return event
    return None


def get_events_for_date(month_day: str) -> dict | None:
    """Get event for a specific MM-DD date."""
    for event in EVENTS:
        if event["date"] == month_day:
            return event
    return None
