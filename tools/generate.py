#!/usr/bin/env python3
"""Generates every per-geode file for Plus Geodes from tools/geodes.json.

Outputs:
  * src/main/java/com/plusgeodes/registry/GeodeTypes.java
  * textures (procedurally drawn, original pixel art), block/item models, blockstates, lang
  * loot tables, recipes, recipe advancements, tags
  * worldgen configured/placed features

Run from anywhere:  python3 tools/generate.py
Requires Pillow (pip install pillow).
"""
import colorsys
import json
import math
import random
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

MOD_ID = "plus_geodes"
ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "src" / "main" / "resources"
ASSETS = RES / "assets" / MOD_ID
DATA = RES / "data" / MOD_ID
JAVA_OUT = ROOT / "src" / "main" / "java" / "com" / "plusgeodes" / "registry" / "GeodeTypes.java"

DEFAULTS = {
    "style": "faceted",
    "light": 0,
    "dimension": "overworld",
    "biomes": [],
    "rarity": 80,
    "y": [-58, 30],
    "middle": "minecraft:calcite",
    "outer": "minecraft:smooth_basalt",
    "filling": "minecraft:air",
    "crack": 0.95,
    "size": "normal",
    "accent": None,
}

BUD_STAGES = ["small", "medium", "large"]


# --------------------------------------------------------------------------- helpers

def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def rid(path: str) -> str:
    return f"{MOD_ID}:{path}"


def hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def palette(base):
    """Five shades, darkest to brightest, derived from the base colour."""
    black, white = (0, 0, 0), (255, 255, 255)
    return [
        mix(base, black, 0.55),
        mix(base, black, 0.28),
        base,
        mix(base, white, 0.30),
        mix(base, white, 0.62),
    ]


def hue_shift(rgb, amount):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    r, g, b = colorsys.hsv_to_rgb((h + amount) % 1.0, max(s, 0.35), v)
    return (round(r * 255), round(g * 255), round(b * 255))


def rgba(rgb, a=255):
    return (*rgb, a)


def is_cubic(g):
    return g["style"] in ("cubic", "iridescent")


# Bismuth-like oxide sheen: gold, magenta, blue, teal, then round again.
IRIDESCENT_HUES = [0.0, 0.17, 0.45, 0.62, 0.83, 0.31]


def cube_palette(g, pal, i):
    """The palette for the i-th cube: the geode's own, or a rainbow tint for iridescent geodes."""
    if g["style"] != "iridescent":
        return pal
    return palette(hue_shift(hex_rgb(g["color"]), IRIDESCENT_HUES[i % len(IRIDESCENT_HUES)]))


# --------------------------------------------------------------------------- textures

def block_texture(g, rng: random.Random) -> Image.Image:
    pal = palette(hex_rgb(g["color"]))
    accent = hex_rgb(g["accent"]) if g["accent"] else None
    img = Image.new("RGBA", (16, 16))
    px = img.load()
    style = g["style"]

    if is_cubic(g):
        # Tiled cubes with bright top-left edges and dark bottom-right edges.
        for by in range(0, 16, 4):
            off = 2 if (by // 4) % 2 else 0
            for bx in range(-4, 16, 4):
                shade = rng.choice([1, 2, 2, 3])
                cpal = cube_palette(g, pal, rng.randrange(len(IRIDESCENT_HUES))) if style == "iridescent" else pal
                for dy in range(4):
                    for dx in range(4):
                        x, y = (bx + off + dx) % 16, by + dy
                        if dx == 0 or dy == 0:
                            c = cpal[min(shade + 1, 4)]
                        elif dx == 3 or dy == 3:
                            c = cpal[max(shade - 1, 0)]
                        else:
                            c = cpal[shade]
                        px[x, y] = rgba(c)
        if accent:
            for _ in range(6):
                px[rng.randrange(16), rng.randrange(16)] = rgba(mix(accent, pal[1], 0.3))
        return img

    if style == "banded":
        phase = rng.random() * math.tau
        colours = [pal[1], pal[2], pal[3], pal[2], accent or pal[4], pal[2], pal[1], pal[0]]
        for y in range(16):
            for x in range(16):
                # Bands wrap horizontally (the sine period is 16 px) so the texture tiles.
                v = y + 2.2 * math.sin(x / 16 * math.tau + phase) + 0.9 * math.sin(x / 8 * math.tau)
                idx = int(v // 2) % len(colours)
                px[x, y] = rgba(colours[idx])
        for _ in range(5):
            px[rng.randrange(16), rng.randrange(16)] = rgba(pal[4])
        return img

    # faceted / speckled / opal: tiling Voronoi facets.
    points = [(rng.uniform(0, 16), rng.uniform(0, 16)) for _ in range(8)]
    shades = [rng.choice([1, 2, 2, 3, 3]) for _ in points]
    opal_tints = [hue_shift(pal[3], rng.uniform(-0.5, 0.5)) for _ in points]

    def nearest(x, y):
        best = []
        for i, (pxx, pyy) in enumerate(points):
            dx = min(abs(x - pxx), 16 - abs(x - pxx))
            dy = min(abs(y - pyy), 16 - abs(y - pyy))
            best.append((dx * dx + dy * dy, i))
        best.sort()
        return best[0], best[1]

    for y in range(16):
        for x in range(16):
            (d0, i0), (d1, _) = nearest(x + 0.5, y + 0.5)
            edge = math.sqrt(d1) - math.sqrt(d0) < 0.9
            if style == "opal":
                c = mix(opal_tints[i0], pal[3], 0.35)
                if edge:
                    c = mix(c, pal[4], 0.5)
            else:
                c = pal[shades[i0]]
                if edge:
                    c = pal[max(shades[i0] - 1, 0)]
            px[x, y] = rgba(c)

    for _ in range(4):
        px[rng.randrange(16), rng.randrange(16)] = rgba(pal[4])
    if style == "speckled" and accent:
        for _ in range(14):
            x, y = rng.randrange(16), rng.randrange(16)
            px[x, y] = rgba(accent)
    return img


def budding_texture(block: Image.Image, g, rng: random.Random) -> Image.Image:
    pal = palette(hex_rgb(g["color"]))
    img = block.copy()
    px = img.load()
    # A handful of dark sockets with a bright seed crystal in the middle.
    for _ in range(5):
        x, y = rng.randrange(16), rng.randrange(16)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            px[(x + dx) % 16, (y + dy) % 16] = rgba(pal[0])
        px[x, y] = rgba(pal[4])
    return img


def draw_spike(img, cx, h, w, lean, pal, dim=0):
    """Draws a pointed crystal prism standing on the bottom edge."""
    tip = (cx + lean, 15.5 - h)
    shoulder = 15.5 - h * 0.45
    poly = [(cx - w, 16), (cx - w + lean * 0.55, shoulder), tip, (cx + w + lean * 0.55, shoulder), (cx + w, 16)]
    mask = Image.new("L", (16, 16))
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    m = mask.load()
    px = img.load()
    hi, base_i, lo = max(3 - dim, 1), max(2 - dim, 0), max(1 - dim, 0)
    for y in range(16):
        for x in range(16):
            if not m[x, y]:
                continue
            outline = any(
                not (0 <= x + dx < 16 and 0 <= y + dy < 16) or not m[x + dx, y + dy]
                for dx, dy in ((1, 0), (-1, 0), (0, -1))
            )
            # Distance along the spike's axis decides the lit/shaded face.
            axis_x = cx + lean * (16 - y) / max(h, 1)
            if outline:
                c = pal[max(lo - 1, 0)] if x >= axis_x else pal[lo]
            elif x < axis_x - 0.5:
                c = pal[hi]
            elif x > axis_x + 0.5:
                c = pal[lo]
            else:
                c = pal[base_i + 1]
            px[x, y] = rgba(c)
    tx, ty = int(round(tip[0])), int(math.ceil(tip[1]))
    if 0 <= tx < 16 and 0 <= ty < 16 and m[tx, ty]:
        px[tx, ty] = rgba(pal[4])


def draw_cube(img, x, y, s, pal, dim=0):
    """Draws a little isometric-ish cube whose bottom-left front corner is (x, y)."""
    px = img.load()
    top, front, side = pal[max(4 - dim, 1)], pal[max(2 - dim, 0)], pal[max(1 - dim, 0)]
    d = max(1, s // 3)
    for yy in range(y - s + 1, y + 1):
        for xx in range(x, x + s):
            if 0 <= xx < 16 and 0 <= yy < 16:
                edge = xx == x or yy == y
                px[xx, yy] = rgba(pal[max(1 - dim, 0)] if edge else front)
    for i in range(1, d + 1):  # top face
        for xx in range(x + i, x + s + i):
            yy = y - s + 1 - i
            if 0 <= xx < 16 and 0 <= yy < 16:
                px[xx, yy] = rgba(top)
    for i in range(1, d + 1):  # right face
        for yy in range(y - s + 1 - i, y + 1 - i):
            xx = x + s - 1 + i
            if 0 <= xx < 16 and 0 <= yy < 16:
                px[xx, yy] = rgba(side)


SPIKES = {
    "small": [(8, 4, 1.6, 0)],
    "medium": [(6, 5, 1.6, -1), (9, 8, 2.0, 0.5)],
    "large": [(4, 7, 1.7, -1.5), (11, 8, 1.8, 1.5), (8, 11, 2.3, 0)],
    "cluster": [(3, 9, 1.6, -2.5), (13, 9, 1.6, 2.5), (5, 11, 2.0, -1.5), (11, 12, 2.0, 1.5), (8, 15, 2.6, 0)],
}

CUBES = {
    "small": [(6, 15, 4)],
    "medium": [(3, 15, 4), (8, 15, 5)],
    "large": [(2, 15, 5), (8, 15, 6), (5, 10, 4)],
    "cluster": [(1, 15, 5), (9, 15, 6), (4, 15, 5), (3, 10, 5), (8, 9, 5), (6, 5, 4)],
}


def growth_texture(g, stage) -> Image.Image:
    pal = palette(hex_rgb(g["color"]))
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    if is_cubic(g):
        cubes = CUBES[stage]
        for i, (x, y, s) in enumerate(cubes):
            draw_cube(img, x, y, s, cube_palette(g, pal, i), dim=1 if i < len(cubes) - 2 and len(cubes) > 2 else 0)
    else:
        spikes = SPIKES[stage]
        for i, (cx, h, w, lean) in enumerate(spikes):
            draw_spike(img, cx, h, w, lean, pal, dim=1 if i < len(spikes) - 1 and len(spikes) > 2 else 0)
    return img


def shard_texture(g, rng: random.Random) -> Image.Image:
    pal = palette(hex_rgb(g["color"]))
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    if is_cubic(g):
        draw_cube(img, 2, 14, 6, cube_palette(g, pal, 0))
        draw_cube(img, 8, 11, 5, cube_palette(g, pal, 2))
        draw_cube(img, 5, 7, 4, cube_palette(g, pal, 4))
        return img
    poly = [(1, 12), (4, 15), (13, 7), (15, 0), (8, 3)]
    mask = Image.new("L", (16, 16))
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    m = mask.load()
    px = img.load()
    accent = hex_rgb(g["accent"]) if g["accent"] else None
    for y in range(16):
        for x in range(16):
            if not m[x, y]:
                continue
            outline = any(
                not (0 <= x + dx < 16 and 0 <= y + dy < 16) or not m[x + dx, y + dy]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            side = (x + y) - 15  # signed distance from the shard's long axis
            if outline:
                c = pal[0]
            elif side < -1:
                c = pal[3]
            elif side > 1:
                c = pal[1]
            else:
                c = pal[2]
            if g["style"] == "opal" and not outline:
                c = mix(hue_shift(pal[3], (x - y) / 24), c, 0.4)
            px[x, y] = rgba(c)
    for x, y in ((13, 2), (12, 3), (7, 7)):
        px[x, y] = rgba(pal[4])
    if accent and g["style"] in ("speckled", "banded"):
        for x, y in ((8, 7), (5, 11), (10, 5)):
            px[x, y] = rgba(accent)
    return img


def icon_texture(geodes) -> Image.Image:
    """A 128x128 geode cross-section ringed by every geode colour."""
    size, scale = 32, 4
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            dx, dy = x - c, y - c
            r = math.hypot(dx, dy)
            if r > 15:
                continue
            if r > 13:
                col = (60, 62, 68)
            elif r > 11:
                col = (226, 222, 210)
            elif r > 5:
                ang = (math.atan2(dy, dx) + math.pi) / math.tau
                g = geodes[int(ang * len(geodes)) % len(geodes)]
                pal = palette(hex_rgb(g["color"]))
                col = pal[3] if r < 7.5 else pal[2] if r < 9.5 else pal[1]
            else:
                col = (24, 22, 30)
            px[x, y] = rgba(col)
    return img.resize((size * scale, size * scale), Image.NEAREST)


# --------------------------------------------------------------------------- data

def block_ids(gid):
    return {
        "block": f"{gid}_block",
        "budding": f"budding_{gid}",
        "small": f"small_{gid}_bud",
        "medium": f"medium_{gid}_bud",
        "large": f"large_{gid}_bud",
        "cluster": f"{gid}_cluster",
    }


def facing_blockstate(model):
    rot = {
        "up": {}, "down": {"x": 180},
        "north": {"x": 90}, "south": {"x": 90, "y": 180},
        "west": {"x": 90, "y": 270}, "east": {"x": 90, "y": 90},
    }
    return {"variants": {f"facing={f}": {"model": model, **r} for f, r in rot.items()}}


def item_definition(model):
    return {"model": {"type": "minecraft:model", "model": model}}


def survives_explosion_loot(item):
    return {
        "type": "minecraft:block",
        "pools": [{
            "rolls": 1,
            "entries": [{"type": "minecraft:item", "name": item}],
            "conditions": [{"condition": "minecraft:survives_explosion"}],
        }],
        "random_sequence": item.replace(":", ":blocks/", 1),
    }


def silk_touch_condition():
    return {
        "condition": "minecraft:match_tool",
        "predicate": {"predicates": {"minecraft:enchantments": [
            {"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}
        ]}},
    }


def bud_loot(block_id):
    return {
        "type": "minecraft:block",
        "pools": [{
            "rolls": 1,
            "entries": [{"type": "minecraft:item", "name": rid(block_id), "conditions": [silk_touch_condition()]}],
        }],
        "random_sequence": rid("blocks/" + block_id),
    }


def cluster_loot(cluster_id, shard):
    return {
        "type": "minecraft:block",
        "pools": [{
            "rolls": 1,
            "entries": [{
                "type": "minecraft:alternatives",
                "children": [
                    {"type": "minecraft:item", "name": rid(cluster_id), "conditions": [silk_touch_condition()]},
                    {
                        "type": "minecraft:item",
                        "name": rid(shard),
                        "conditions": [{
                            "condition": "minecraft:match_tool",
                            "predicate": {"items": "#minecraft:cluster_max_harvestables"},
                        }],
                        "functions": [
                            {"function": "minecraft:set_count", "count": 4.0, "add": False},
                            {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune",
                             "formula": "minecraft:ore_drops"},
                        ],
                    },
                    {
                        "type": "minecraft:item",
                        "name": rid(shard),
                        "functions": [
                            {"function": "minecraft:set_count", "count": 2.0, "add": False},
                            {"function": "minecraft:explosion_decay"},
                        ],
                    },
                ],
            }],
        }],
        "random_sequence": rid("blocks/" + cluster_id),
    }


def state(name, **props):
    s = {"Name": name}
    if props:
        s["Properties"] = props
    return s


def configured_feature(g, ids):
    large = g["size"] == "large"
    small = g["size"] == "small"
    return {
        "type": "minecraft:geode",
        "config": {
            "blocks": {
                "filling_provider": {"type": "minecraft:simple_state_provider", "state": state(g["filling"])},
                "inner_layer_provider": {"type": "minecraft:simple_state_provider", "state": state(rid(ids["block"]))},
                "alternate_inner_layer_provider": {"type": "minecraft:simple_state_provider",
                                                   "state": state(rid(ids["budding"]))},
                "middle_layer_provider": {"type": "minecraft:simple_state_provider", "state": state(g["middle"])},
                "outer_layer_provider": {"type": "minecraft:simple_state_provider", "state": state(g["outer"])},
                "inner_placements": [
                    state(rid(ids[k]), facing="up", waterlogged="false")
                    for k in ("small", "medium", "large", "cluster")
                ],
                "cannot_replace": "#minecraft:features_cannot_replace",
                "invalid_blocks": "#minecraft:geode_invalid_blocks",
            },
            "layers": {"filling": 1.7, "inner_layer": 2.2, "middle_layer": 3.2, "outer_layer": 4.2},
            "crack": {"generate_crack_chance": g["crack"], "base_crack_size": 2.0, "crack_point_offset": 2},
            "noise_multiplier": 0.05,
            "use_potential_placements_chance": 0.35,
            "use_alternate_layer0_chance": 0.083,
            "placements_require_layer0_alternate": True,
            "outer_wall_distance": {"type": "minecraft:uniform",
                                    "min_inclusive": 3 if small else 5 if large else 4,
                                    "max_inclusive": 5 if small else 7 if large else 6},
            "distribution_points": {"type": "minecraft:uniform",
                                    "min_inclusive": 2 if small else 4 if large else 3,
                                    "max_inclusive": 3 if small else 5 if large else 4},
            "point_offset": {"type": "minecraft:uniform", "min_inclusive": 1, "max_inclusive": 2},
            "min_gen_offset": -16,
            "max_gen_offset": 16,
            "invalid_blocks_threshold": 1,
        },
    }


def placed_feature(g):
    lo, hi = g["y"]
    placement = [
        {"type": "minecraft:rarity_filter", "chance": g["rarity"]},
        {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {
            "type": "minecraft:uniform",
            "min_inclusive": {"absolute": lo},
            "max_inclusive": {"absolute": hi},
        }},
    ]
    # Keep nether/end geodes anchored inside terrain instead of floating in open air or the void.
    if g["dimension"] == "end":
        placement.append({"type": "minecraft:block_predicate_filter",
                          "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:end_stone"}})
    elif g["dimension"] == "nether":
        placement.append({"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:solid"}})
    placement.append({"type": "minecraft:biome"})
    return {"feature": rid(f"{g['id']}_geode"), "placement": placement}


def shaped_recipe(pattern, key, result, count=1, group=None):
    r = {
        "type": "minecraft:crafting_shaped",
        "category": "building",
        "pattern": pattern,
        "key": key,
        "result": {"id": result, "count": count},
    }
    if group:
        r["group"] = group
    return r


def recipe_advancement(recipe_id, trigger_item):
    return {
        "parent": "minecraft:recipes/root",
        "criteria": {
            "has_the_recipe": {"trigger": "minecraft:recipe_unlocked", "conditions": {"recipe": recipe_id}},
            "has_item": {"trigger": "minecraft:inventory_changed",
                         "conditions": {"items": [{"items": trigger_item}]}},
        },
        "requirements": [["has_the_recipe", "has_item"]],
        "rewards": {"recipes": [recipe_id]},
    }


# --------------------------------------------------------------------------- java

def java_source(geodes):
    lines = []
    for g in geodes:
        biomes = ", ".join(json.dumps(b) for b in g["biomes"])
        lines.append(
            f'        new GeodeType("{g["id"]}", MapColor.{g["map_color"]}, {g["light"]}, '
            f'GeodeType.Dimension.{g["dimension"].upper()}, List.of({biomes}))'
        )
    body = ",\n".join(lines)
    return f"""// GENERATED FILE - do not edit by hand.
// Edit tools/geodes.json and run `python3 tools/generate.py` instead.
package com.plusgeodes.registry;

import java.util.List;
import net.minecraft.world.level.material.MapColor;

public final class GeodeTypes {{
    public static final List<GeodeType> ALL = List.of(
{body}
    );

    private GeodeTypes() {{
    }}
}}
"""


# --------------------------------------------------------------------------- main

def main():
    raw = json.loads((ROOT / "tools" / "geodes.json").read_text(encoding="utf-8"))
    geodes = [{**DEFAULTS, **g} for g in raw["geodes"]]
    seen = set()
    for g in geodes:
        assert g["id"] not in seen, f"duplicate geode id {g['id']}"
        seen.add(g["id"])
        assert g["dimension"] in ("overworld", "nether", "end"), g["id"]
        assert g["style"] in ("faceted", "cubic", "banded", "speckled", "opal", "iridescent"), g["id"]

    # Wipe directories that are entirely generated so removed geodes leave nothing behind.
    for d in [
        ASSETS / "blockstates", ASSETS / "items", ASSETS / "models", ASSETS / "textures",
        DATA / "loot_table", DATA / "recipe", DATA / "advancement", DATA / "worldgen", DATA / "tags",
        RES / "data" / "minecraft" / "tags", RES / "data" / "c" / "tags",
    ]:
        shutil.rmtree(d, ignore_errors=True)

    lang = {"itemGroup.plus_geodes": "Plus Geodes"}
    all_blocks, crystal_blocks, budding_blocks, cluster_blocks, shards = [], [], [], [], []

    for g in geodes:
        gid, name = g["id"], g["name"]
        ids = block_ids(gid)
        shard = f"{gid}_shard"
        rng = random.Random(gid)

        # textures
        tex_block = ASSETS / "textures" / "block"
        tex_item = ASSETS / "textures" / "item"
        tex_block.mkdir(parents=True, exist_ok=True)
        tex_item.mkdir(parents=True, exist_ok=True)
        block_img = block_texture(g, rng)
        block_img.save(tex_block / f"{ids['block']}.png")
        budding_texture(block_img, g, rng).save(tex_block / f"{ids['budding']}.png")
        for stage in BUD_STAGES + ["cluster"]:
            growth_texture(g, stage).save(tex_block / f"{ids[stage]}.png")
        shard_texture(g, rng).save(tex_item / f"{shard}.png")

        # block models + blockstates + item models
        for key in ("block", "budding"):
            b = ids[key]
            write_json(ASSETS / "models" / "block" / f"{b}.json",
                       {"parent": "minecraft:block/cube_all", "textures": {"all": rid(f"block/{b}")}})
            write_json(ASSETS / "blockstates" / f"{b}.json", {"variants": {"": {"model": rid(f"block/{b}")}}})
            write_json(ASSETS / "items" / f"{b}.json", item_definition(rid(f"block/{b}")))
        for key in BUD_STAGES + ["cluster"]:
            b = ids[key]
            write_json(ASSETS / "models" / "block" / f"{b}.json",
                       {"parent": "minecraft:block/cross", "textures": {"cross": rid(f"block/{b}")}})
            write_json(ASSETS / "blockstates" / f"{b}.json", facing_blockstate(rid(f"block/{b}")))
            write_json(ASSETS / "models" / "item" / f"{b}.json", {
                "parent": "minecraft:item/amethyst_bud",
                "textures": {"layer0": rid(f"block/{b}")},
            })
            write_json(ASSETS / "items" / f"{b}.json", item_definition(rid(f"item/{b}")))
        write_json(ASSETS / "models" / "item" / f"{shard}.json",
                   {"parent": "minecraft:item/generated", "textures": {"layer0": rid(f"item/{shard}")}})
        write_json(ASSETS / "items" / f"{shard}.json", item_definition(rid(f"item/{shard}")))

        # lang
        lang[f"block.{MOD_ID}.{ids['block']}"] = f"Block of {name}"
        lang[f"block.{MOD_ID}.{ids['budding']}"] = f"Budding {name}"
        lang[f"block.{MOD_ID}.{ids['small']}"] = f"Small {name} Bud"
        lang[f"block.{MOD_ID}.{ids['medium']}"] = f"Medium {name} Bud"
        lang[f"block.{MOD_ID}.{ids['large']}"] = f"Large {name} Bud"
        lang[f"block.{MOD_ID}.{ids['cluster']}"] = f"{name} Cluster"
        lang[f"item.{MOD_ID}.{shard}"] = f"{name} Shard"

        # loot tables
        lt = DATA / "loot_table" / "blocks"
        write_json(lt / f"{ids['block']}.json", survives_explosion_loot(rid(ids["block"])))
        write_json(lt / f"{ids['budding']}.json", {"type": "minecraft:block", "random_sequence": rid("blocks/" + ids["budding"])})
        for stage in BUD_STAGES:
            write_json(lt / f"{ids[stage]}.json", bud_loot(ids[stage]))
        write_json(lt / f"{ids['cluster']}.json", cluster_loot(ids["cluster"], shard))

        # recipes
        block_recipe = rid(ids["block"])
        write_json(DATA / "recipe" / f"{ids['block']}.json",
                   shaped_recipe(["##", "##"], {"#": rid(shard)}, rid(ids["block"])))
        write_json(DATA / "advancement" / "recipes" / "building_blocks" / f"{ids['block']}.json",
                   recipe_advancement(block_recipe, rid(shard)))

        # worldgen
        write_json(DATA / "worldgen" / "configured_feature" / f"{gid}_geode.json", configured_feature(g, ids))
        write_json(DATA / "worldgen" / "placed_feature" / f"{gid}_geode.json", placed_feature(g))

        all_blocks += [rid(v) for v in ids.values()]
        crystal_blocks += [rid(ids["block"]), rid(ids["budding"])]
        budding_blocks.append(rid(ids["budding"]))
        cluster_blocks += [rid(ids[k]) for k in BUD_STAGES + ["cluster"]]
        shards.append(rid(shard))

    # tags
    write_json(RES / "data" / "minecraft" / "tags" / "block" / "mineable" / "pickaxe.json",
               {"replace": False, "values": all_blocks})
    write_json(RES / "data" / "minecraft" / "tags" / "block" / "crystal_sound_blocks.json",
               {"replace": False, "values": crystal_blocks})
    write_json(DATA / "tags" / "block" / "budding_crystals.json", {"replace": False, "values": budding_blocks})
    write_json(DATA / "tags" / "block" / "crystal_clusters.json", {"replace": False, "values": cluster_blocks})
    write_json(DATA / "tags" / "item" / "shards.json", {"replace": False, "values": shards})
    write_json(RES / "data" / "c" / "tags" / "item" / "gems.json", {"replace": False, "values": shards})

    write_json(ASSETS / "lang" / "en_us.json", lang)
    icon_texture(geodes).save(ASSETS / "icon.png")

    JAVA_OUT.parent.mkdir(parents=True, exist_ok=True)
    JAVA_OUT.write_text(java_source(geodes), encoding="utf-8")
    print(f"Generated {len(geodes)} geodes.")


if __name__ == "__main__":
    main()
