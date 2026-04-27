#!/usr/bin/env python3
"""
TMX to Phaser-compatible JSON tilemap converter.
Supports both inline and external (.tsx) tilesets.
"""

import xml.etree.ElementTree as ET
import json
import sys
import os

TMX_PATH = "tiled-project/cozy-claw.tmx"
OUTPUT_PATH = "map_tiled.json"


def parse_tsx(tsx_path):
    """Parse an external .tsx tileset file."""
    tree = ET.parse(tsx_path)
    root = tree.getroot()
    img = root.find("image")
    return {
        "name": root.get("name"),
        "tilewidth": int(root.get("tilewidth", 16)),
        "tileheight": int(root.get("tileheight", 16)),
        "tilecount": int(root.get("tilecount", 0)),
        "columns": int(root.get("columns", 1)),
        "image_source": img.get("source") if img is not None else None,
        "imagewidth": int(img.get("width", 0)) if img is not None else 0,
        "imageheight": int(img.get("height", 0)) if img is not None else 0,
    }


def parse_tmx(tmx_path):
    tree = ET.parse(tmx_path)
    root = tree.getroot()
    tmx_dir = os.path.dirname(os.path.abspath(tmx_path))

    map_width = int(root.get("width"))
    map_height = int(root.get("height"))
    tile_width = int(root.get("tilewidth"))
    tile_height = int(root.get("tileheight"))

    # Parse tilesets (inline or external .tsx)
    tilesets = []
    for ts in root.findall("tileset"):
        firstgid = int(ts.get("firstgid"))
        source = ts.get("source")

        if source:
            # External .tsx file
            tsx_path = os.path.join(tmx_dir, source)
            tsx_data = parse_tsx(tsx_path)
            name = tsx_data["name"]
            tw = tsx_data["tilewidth"]
            th = tsx_data["tileheight"]
            tc = tsx_data["tilecount"]
            cols = tsx_data["columns"]
            iw = tsx_data["imagewidth"]
            ih = tsx_data["imageheight"]
            # Image path: tsx references relative to tsx location
            img_source = tsx_data["image_source"]
        else:
            # Inline tileset
            name = ts.get("name")
            tw = int(ts.get("tilewidth", 16))
            th = int(ts.get("tileheight", 16))
            tc = int(ts.get("tilecount", 0))
            cols = int(ts.get("columns", 1))
            img = ts.find("image")
            if img is not None:
                iw = int(img.get("width", 0))
                ih = int(img.get("height", 0))
                img_source = img.get("source")
            else:
                iw, ih = 0, 0
                img_source = None

        # Resolve image path for Phaser (relative to game root)
        if img_source:
            # Check if it's a merged tileset (starts with tilesets_merged/)
            if "tilesets_merged/" in img_source:
                # Use the sprites directory
                basename = os.path.basename(img_source)
                phaser_image = "assets/sprites/" + basename
            elif "tilesets/" in img_source:
                # New tilesets added by user - copy to assets/sprites/
                basename = os.path.basename(img_source)
                phaser_image = "assets/sprites/" + basename
                # Ensure the file exists in assets/sprites/
                src_file = os.path.join(tmx_dir, img_source)
                dst_file = os.path.join(os.path.dirname(tmx_dir), "assets", "sprites", basename)
                if os.path.exists(src_file) and not os.path.exists(dst_file):
                    import shutil
                    shutil.copy2(src_file, dst_file)
                    print(f"  Copied {basename} to assets/sprites/")
            else:
                basename = os.path.basename(img_source)
                phaser_image = "assets/sprites/" + basename
        else:
            phaser_image = "assets/sprites/" + name + ".png"

        tileset = {
            "firstgid": firstgid,
            "name": name,
            "tilewidth": tw,
            "tileheight": th,
            "tilecount": tc,
            "columns": cols,
            "image": phaser_image,
            "imagewidth": iw,
            "imageheight": ih,
            "margin": 0,
            "spacing": 0
        }
        tilesets.append(tileset)

    # Parse tile layers
    layers = []
    for layer in root.findall("layer"):
        data_el = layer.find("data")
        encoding = data_el.get("encoding", "")
        if encoding == "csv":
            raw = data_el.text.strip()
            tile_data = [int(x) for x in raw.replace("\n", "").split(",") if x.strip()]
        else:
            tile_data = []

        layer_obj = {
            "id": int(layer.get("id")),
            "name": layer.get("name"),
            "type": "tilelayer",
            "width": int(layer.get("width")),
            "height": int(layer.get("height")),
            "x": 0,
            "y": 0,
            "visible": True,
            "opacity": 1,
            "data": tile_data
        }
        layers.append(layer_obj)

    # Parse object groups (Markers layer)
    for og in root.findall("objectgroup"):
        objects = []
        for obj in og.findall("object"):
            o = {
                "id": int(obj.get("id", 0)),
                "name": obj.get("name", ""),
                "type": obj.get("type", ""),
                "x": float(obj.get("x", 0)),
                "y": float(obj.get("y", 0)),
                "width": float(obj.get("width", 0)),
                "height": float(obj.get("height", 0)),
                "visible": True
            }
            objects.append(o)

        layer_obj = {
            "id": int(og.get("id")),
            "name": og.get("name"),
            "type": "objectgroup",
            "x": 0,
            "y": 0,
            "visible": True,
            "opacity": 1,
            "objects": objects
        }
        layers.append(layer_obj)

    # Build Phaser-compatible tilemap JSON
    tilemap = {
        "compressionlevel": -1,
        "height": map_height,
        "width": map_width,
        "tileheight": tile_height,
        "tilewidth": tile_width,
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "tiledversion": "1.11.2",
        "type": "map",
        "version": "1.10",
        "infinite": False,
        "layers": layers,
        "tilesets": tilesets,
        "nextlayerid": int(root.get("nextlayerid", 10)),
        "nextobjectid": int(root.get("nextobjectid", 1))
    }

    return tilemap


def main():
    tmx_path = sys.argv[1] if len(sys.argv) > 1 else TMX_PATH
    output_path = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_PATH

    tilemap = parse_tmx(tmx_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tilemap, f)

    print(f"Converted {tmx_path} -> {output_path}")
    print(f"  Map: {tilemap['width']}x{tilemap['height']} tiles ({tilemap['tilewidth']}px)")
    print(f"  Layers: {len(tilemap['layers'])}")
    print(f"  Tilesets: {len(tilemap['tilesets'])}")
    for ts in tilemap["tilesets"]:
        print(f"    {ts['name']}: firstgid={ts['firstgid']}, {ts['tilecount']} tiles, image={ts['image']}")

    # Show markers
    for layer in tilemap["layers"]:
        if layer["type"] == "objectgroup":
            print(f"  Markers ({layer['name']}):")
            for obj in layer.get("objects", []):
                print(f"    {obj['name']}: x={obj['x']}, y={obj['y']}")


if __name__ == "__main__":
    main()
