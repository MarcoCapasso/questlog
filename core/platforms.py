"""Nomi delle piattaforme: un solo nome per ogni console, qualunque sia il modo in cui è stato scritto."""

from core.models import Game

PLATFORM_ALIASES = {
    "PC": ["pc", "windows", "pc (microsoft windows)", "microsoft windows"],
    "Mac": ["mac", "macos", "mac os"],
    "Linux": ["linux"],
    "iOS": ["ios", "iphone", "ipad"],
    "Android": ["android"],
    "PlayStation": ["ps1", "psx", "ps one", "playstation", "playstation 1"],
    "PlayStation 2": ["ps2", "playstation 2"],
    "PlayStation 3": ["ps3", "playstation 3"],
    "PlayStation 4": ["ps4", "playstation 4"],
    "PlayStation 5": ["ps5", "playstation 5"],
    "PSP": ["psp", "playstation portable"],
    "PlayStation Vita": ["ps vita", "psvita", "vita", "playstation vita"],
    "Xbox": ["xbox", "original xbox"],
    "Xbox 360": ["xbox 360", "x360"],
    "Xbox One": ["xbox one", "xone", "xb1"],
    "Xbox Series X|S": ["xbox series x|s", "xbox series x", "xbox series s", "series x", "series s", "xsx"],
    "NES": ["nes", "nintendo entertainment system"],
    "Super Nintendo": ["snes", "super nintendo", "super nintendo entertainment system", "super famicom"],
    "Nintendo 64": ["n64", "nintendo 64"],
    "Nintendo GameCube": ["gamecube", "gc", "ngc", "nintendo gamecube"],
    "Wii": ["wii"],
    "Wii U": ["wii u", "wiiu"],
    "Nintendo Switch": ["switch", "nintendo switch", "ns", "nsw"],
    "Nintendo Switch 2": ["switch 2", "switch2", "nintendo switch 2", "ns2", "nsw2"],
    "Game Boy": ["game boy", "gameboy", "gb"],
    "Game Boy Color": ["game boy color", "gbc"],
    "Game Boy Advance": ["game boy advance", "gba"],
    "Nintendo DS": ["ds", "nds", "nintendo ds"],
    "Nintendo 3DS": ["3ds", "nintendo 3ds", "new nintendo 3ds"],
}

CANONICAL_NAMES = {
    alias: name
    for name, aliases in PLATFORM_ALIASES.items()
    for alias in aliases
}


def normalize_platform(platform: str) -> str:
    """Restituisce il nome ufficiale della piattaforma ("ps4" → "PlayStation 4").

    Le piattaforme sconosciute (per esempio "Steam Deck") restano come sono, solo senza spazi in eccesso.
    """
    clean_name = " ".join(platform.split())
    return CANONICAL_NAMES.get(clean_name.lower(), clean_name)


def normalize_platforms(platforms: list[str]) -> list[str]:
    """Normalizza un elenco di piattaforme togliendo i doppioni e mantenendo l'ordine."""
    result: list[str] = []
    for platform in platforms:
        name = normalize_platform(platform)
        if name not in result:
            result.append(name)
    return result


def normalize_library_platforms(games: list[Game]) -> int:
    """Normalizza le piattaforme di tutte le partite della libreria; restituisce quante sono cambiate."""
    changed = 0
    for game in games:
        for playthrough in game.playthroughs:
            name = normalize_platform(playthrough.platform)
            if name != playthrough.platform:
                playthrough.platform = name
                changed += 1
    return changed
