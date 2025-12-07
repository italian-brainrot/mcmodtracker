from typing import Literal

HEADERS = {
    "User-Agent": "italian-brainrot/mcmodtracker/1.0.0 (updtae@gmail.com)"
}


ProjectType = Literal['mod', 'modpack', 'resourcepack', 'shader', 'plugin', 'datapack'] | str

Category = Literal["128x", "16x", "256x", "32x", "48x", "512x+", "64x", "8x-", "adventure", "adventure", "atmosphere", "audio", "blocks", "bloom", "cartoon", "challenging", "colored-lighting", "combat", "combat", "core-shaders", "cursed", "cursed", "cursed", "decoration", "decoration", "economy", "entities", "environment", "equipment", "equipment", "fantasy", "foliage", "fonts", "food", "game-mechanics", "gui", "high", "items", "kitchen-sink", "library", "lightweight", "locale", "low", "magic", "magic", "management", "medium", "minigame", "mobs", "modded", "models", "multiplayer", "optimization", "optimization", "path-tracing", "pbr", "potato", "quests", "realistic", "realistic", "reflections", "screenshot", "semi-realistic", "shadows", "simplistic", "social", "storage", "technology", "technology", "themed", "transportation", "tweaks", "utility", "utility", "vanilla-like", "vanilla-like", "worldgen"] | str

Loader = Literal["babric", "bta-babric", "bukkit", "bungeecord", "canvas", "datapack", "fabric", "folia", "forge", "geyser", "iris", "java-agent", "legacy-fabric", "liteloader", "minecraft", "modloader", "neoforge", "nilloader", "optifine", "ornithe", "paper", "purpur", "quilt", "rift", "spigot", "sponge", "vanilla", "velocity", "waterfall"] | str

Index = Literal["relevance", "downloads", "follows", "newest", "updated"]