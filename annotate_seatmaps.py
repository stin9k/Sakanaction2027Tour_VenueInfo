#!/usr/bin/env python3
"""Annotate SAKANAQUARIUM seat maps with explicit data-safety modes."""

import argparse
from collections import deque
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WORKDIR = Path(__file__).parent
ORIGINAL_DIR = WORKDIR / "original"
ANNOTATED_DIR = WORKDIR / "annotated"
ZONE_ONLY_DIR = WORKDIR / "annotated_zones"
UNVERIFIED_DIR = WORKDIR / "annotated_unverified"
FONT_PATH = "/System/Library/Fonts/STHeiti Light.ttc"
FONT_BOLD = "/Library/Fonts/Arial Unicode.ttf"

VALID_CONFIDENCE_LEVELS = {"confirmed", "approximate", "unverified", "rejected"}

# zone_key -> (label, color)
ZONE_COLORS = {
    "SS": ("SS席", "#C0392B"),
    "S": ("S席", "#2C3E8C"),
    "A": ("A席", "#D35400"),
    "B": ("B席", "#1ABC9C"),
}

ZONE_RGB = {
    "SS": (255, 90, 90),
    "S": (70, 120, 200),
    "A": (255, 140, 40),
    "B": (60, 190, 190),
}

# Historical estimate inputs. These are blocked by default and must not be
# treated as verified venue specifications; see venues_Dataset.md.
VENUES = {
    "seatmap_hiroshima": {
        "name": "広島グリーンアリーナ",
        "name_zh": "廣島格林アリーナ",
        "size": "48m × 80m",
        "area": "3,500㎡",
        "capacity_status": "unverified",
        "dimension_status": "unverified",
        "total": 10000,
        "floor_capacity": 5250,
        "stand_capacity": 4750,
        "floor_s_components": [1, 2, 3, 4],
        "zones": {"SS": {}, "S": {}, "A": {}, "B": {}},
    },
    "seatmap_anabuki": {
        "name": "あなぶきアリーナ香川",
        "name_zh": "穴吹アリーナ香川",
        "size": "78m × 48m",
        "area": "3,385㎡",
        "capacity_status": "unverified",
        "dimension_status": "unverified",
        "total": 10000,
        "floor_capacity": 5000,
        "stand_capacity": 5000,
        "floor_s_components": [1, 2, 3, 4],
        "zones": {"SS": {}, "S": {}, "A": {}, "B": {}},
    },
    "seatmap_marinmesse": {
        "name": "マリンメッセ福岡 A館",
        "name_zh": "Marine Messe 福岡 A館",
        "size": "約 8,000㎡",
        "area": "アリーナ面",
        "capacity_status": "unverified",
        "dimension_status": "unverified",
        "total": 15000,
        "floor_capacity": 9000,
        "stand_capacity": 6000,
        "floor_s_components": [1, 2],
        "zones": {"SS": {}, "S": {}, "A": {}, "B": {}},
    },
    "seatmap_lala": {
        "name": "ららアリーナ 東京ベイ",
        "name_zh": "LaLa arena 東京灣",
        "size": "約 11,000人規模",
        "area": "延床 31,000㎡",
        "capacity_status": "unverified",
        "dimension_status": "unverified",
        "total": 11000,
        "floor_capacity": 5000,
        "stand_capacity": 6000,
        "floor_s_components": [2, 3],
        "zones": {"SS": {}, "S": {}, "A": {}, "B": {}},
    },
    "seatmap_kobe": {
        "name": "GLION ARENA KOBE",
        "name_zh": "GLION ARENA 神戶",
        "size": "43.7m × 48.0m",
        "area": "2,096㎡",
        "capacity_status": "rejected",
        "dimension_status": "unverified",
        "total": 10000,
        "floor_capacity": 4500,
        "stand_capacity": 5500,
        "floor_s_components": [1, 3, 4],
        "zones": {"SS": {}, "S": {}, "A": {}, "B": {}},
    },
    "seatmap_zevioarena": {
        "name": "ゼビオアリーナ仙台",
        "name_zh": "Xebio Arena 仙台",
        "size": "約 2,170㎡",
        "area": "アリーナ面",
        "capacity_status": "rejected",
        "dimension_status": "approximate",
        "total": 7200,
        "floor_capacity": 3200,
        "stand_capacity": 4000,
        "floor_s_components": [1, 2],
        "zones": {"SS": {}, "S": {}, "A": {}, "B": {}},
    },
    "seatmap_kitaeru": {
        "name": "北海きたえーる",
        "name_zh": "北海 Kitayell",
        "size": "84.3m × 49.7m",
        "area": "3,886㎡",
        "capacity_status": "rejected",
        "dimension_status": "unverified",
        "total": 10000,
        "floor_capacity": 4000,
        "stand_capacity": 6000,
        "floor_s_components": [0, 1],
        "zones": {"SS": {}, "S": {}, "A": {}, "B": {}},
    },
    "seatmap_portmesse": {
        "name": "ポートメッセなごや 第一展示館",
        "name_zh": "Port Messe 名古屋 第一展示館",
        "size": "210m × 96m",
        "area": "20,160㎡",
        "capacity_status": "approximate",
        "dimension_status": "unverified",
        "total": 15000,
        "floor_capacity": 15000,
        "stand_capacity": 0,
        "floor_s_components": [0, 1, 2],
        "zones": {"SS": {}, "S": {}, "A": {}},
    },
    "seatmap_sundom": {
        "name": "サンドーム福井",
        "name_zh": "Sun Dome 福井",
        "size": "直徑 116m",
        "area": "約 8,000㎡",
        "capacity_status": "rejected",
        "dimension_status": "confirmed",
        "dimension_scope": "building",
        "total": 10000,
        "floor_capacity": 4000,
        "stand_capacity": 6000,
        "floor_s_components": [0, 1],
        "zones": {"SS": {}, "S": {}, "A": {}, "B": {}},
    },
}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_PATH
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def format_count(n: int) -> str:
    return f"{n:,}"


def match_zone_color(px):
    if max(px) < 50 or (max(px) - min(px) < 15 and min(px) > 180):
        return None
    best_zone = None
    best_dist = 999.0
    for zone, ref in ZONE_RGB.items():
        dist = sum((a - b) ** 2 for a, b in zip(px, ref)) ** 0.5
        if dist < best_dist:
            best_dist = dist
            best_zone = zone
    return best_zone if best_dist < 70 else None


def find_zone_components(img, zone, step=2):
    pxmap = img.load()
    w, h = img.size
    visited = set()
    components = []

    def is_zone(x: int, y: int) -> bool:
        return match_zone_color(pxmap[x, y]) == zone

    for start_y in range(0, h, step):
        for start_x in range(0, w, step):
            if (start_x, start_y) in visited or not is_zone(start_x, start_y):
                continue

            queue = deque([(start_x, start_y)])
            visited.add((start_x, start_y))
            points = []

            while queue:
                x, y = queue.popleft()
                points.append((x, y))
                for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < w
                        and 0 <= ny < h
                        and (nx, ny) not in visited
                        and is_zone(nx, ny)
                    ):
                        visited.add((nx, ny))
                        queue.append((nx, ny))

            if len(points) < 350:
                continue

            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            cx = sum(xs) / len(points)
            cy = sum(ys) / len(points)
            if cx / w > 0.85 and cy / h > 0.80:
                continue
            components.append(
                {
                    "rx": cx / w,
                    "ry": cy / h,
                    "pts": len(points),
                    "min_rx": min_x / w,
                    "max_rx": max_x / w,
                    "min_ry": min_y / h,
                    "max_ry": max_y / h,
                }
            )

    components.sort(key=lambda item: item["pts"], reverse=True)
    return components


def anchor_badge_center(component, w, h, header_h, box_w, box_h):
    min_rx = component["min_rx"]
    max_rx = component["max_rx"]
    min_ry = component["min_ry"]
    max_ry = component["max_ry"]
    cx = int((min_rx + max_rx) * 0.5 * w)
    comp_h = (max_ry - min_ry) * h
    comp_w = (max_rx - min_rx) * w

    if comp_h < box_h * 0.75 and comp_w >= comp_h:
        cy = int((min_ry + max_ry) * 0.5 * h) + header_h
    else:
        cy = int(component["ry"] * h) + header_h

    return cx, cy


def component_tier(venue, zone_key, component_index):
    """Classify a colored component as 1F floor or elevated stand."""
    if venue["stand_capacity"] == 0:
        return "floor"
    if zone_key == "SS":
        return "floor"
    if zone_key == "S" and component_index in venue["floor_s_components"]:
        return "floor"
    return "stand"


def allocate_integer(total, weights):
    """Allocate an integer total proportionally while preserving the exact sum."""
    if total == 0:
        return {key: 0 for key in weights}
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        raise ValueError("Cannot allocate capacity without positive component area")

    raw = {key: total * weight / weight_sum for key, weight in weights.items()}
    allocated = {key: int(value) for key, value in raw.items()}
    remainder = total - sum(allocated.values())
    order = sorted(
        raw,
        key=lambda key: raw[key] - allocated[key],
        reverse=True,
    )
    for key in order[:remainder]:
        allocated[key] += 1
    return allocated


def calculate_zone_allocations(venue, zone_components):
    """Split floor/stand capacities, then combine them into ticket-zone totals."""
    area_by_tier = {"floor": {}, "stand": {}}
    for zone_key, components in zone_components.items():
        for index, component in enumerate(components):
            tier = component_tier(venue, zone_key, index)
            tier_areas = area_by_tier[tier]
            tier_areas[zone_key] = tier_areas.get(zone_key, 0) + component["pts"]

    floor_counts = allocate_integer(venue["floor_capacity"], area_by_tier["floor"])
    stand_counts = allocate_integer(venue["stand_capacity"], area_by_tier["stand"])

    totals = {}
    for zone_key in zone_components:
        floor_count = floor_counts.get(zone_key, 0)
        stand_count = stand_counts.get(zone_key, 0)
        count = floor_count + stand_count
        if floor_count and stand_count:
            tier_label = "1F＋看台"
        elif floor_count:
            tier_label = "1F"
        else:
            tier_label = "看台"
        totals[zone_key] = {
            "count": count,
            "floor_count": floor_count,
            "stand_count": stand_count,
            "tier": tier_label,
            "estimated": True,
        }

    percentages = allocate_integer(
        100,
        {zone_key: data["count"] for zone_key, data in totals.items()},
    )
    for zone_key, percentage in percentages.items():
        totals[zone_key]["pct"] = percentage

    validate_allocations(venue, totals)
    return totals


def validate_allocations(venue, zones):
    floor_total = sum(zone["floor_count"] for zone in zones.values())
    stand_total = sum(zone["stand_count"] for zone in zones.values())
    total = sum(zone["count"] for zone in zones.values())
    percentage_total = sum(zone["pct"] for zone in zones.values())

    if floor_total != venue["floor_capacity"]:
        raise ValueError(f"{venue['name']}: 1F allocation is {floor_total}")
    if stand_total != venue["stand_capacity"]:
        raise ValueError(f"{venue['name']}: stand allocation is {stand_total}")
    if total != venue["total"]:
        raise ValueError(f"{venue['name']}: total allocation is {total}")
    if percentage_total != 100:
        raise ValueError(f"{venue['name']}: percentages total {percentage_total}%")


def badge_lines(zone_key, zone_data):
    if not zone_data.get("estimated", False):
        return [zone_key, "區域示意"]
    lines = [
        f"{zone_key}（{zone_data['tier']}）",
        f"{format_count(zone_data['count'])}人",
        f"{zone_data['pct']}%",
    ]
    return lines


def line_fonts(fonts):
    return [fonts["lg"], fonts["md"], fonts["sm"], fonts["sm"]]


def measure_text_block(draw, lines, fonts, pad_x=14, pad_y=10, line_gap=4):
    line_heights = []
    max_w = 0
    for i, line in enumerate(lines):
        f = line_fonts(fonts)[min(i, len(line_fonts(fonts)) - 1)]
        bbox = draw.textbbox((0, 0), line, font=f)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        line_heights.append((line, f, h))

    box_w = max_w + pad_x * 2
    box_h = sum(h for _, _, h in line_heights) + pad_y * 2 + (len(lines) - 1) * line_gap
    return line_heights, box_w, box_h


def rect_at_center(cx, cy, box_w, box_h):
    x0 = cx - box_w // 2
    y0 = cy - box_h // 2
    return (x0, y0, x0 + box_w, y0 + box_h)


def rects_overlap(a, b, margin=14):
    return not (
        a[2] + margin < b[0]
        or b[2] + margin < a[0]
        or a[3] + margin < b[1]
        or b[3] + margin < a[1]
    )


def draw_zone_badge(draw, cx, cy, zone_key, zone_data, fonts):
    """Draw a compact label badge on the map."""
    _, color = ZONE_COLORS[zone_key]
    lines = badge_lines(zone_key, zone_data)
    line_heights, box_w, box_h = measure_text_block(draw, lines, fonts)
    pad_y = 10
    line_gap = 4

    x0, y0, x1, y1 = rect_at_center(cx, cy, box_w, box_h)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill="#FFFFFFEE", outline=color, width=3)

    y = y0 + pad_y
    for line, f, h in line_heights:
        bbox = draw.textbbox((0, 0), line, font=f)
        w = bbox[2] - bbox[0]
        draw.text((cx - w // 2, y), line, fill="#222222", font=f)
        y += h + line_gap


def measure_full_badge_rect(draw, cx, cy, zone_key, zone_data, fonts):
    lines = badge_lines(zone_key, zone_data)
    _, box_w, box_h = measure_text_block(draw, lines, fonts)
    return rect_at_center(cx, cy, box_w, box_h)


def measure_mini_badge_rect(draw, cx, cy, zone_key, zone_data, fonts):
    text = (
        f"{zone_key} {zone_data['pct']}%"
        if zone_data.get("estimated", False)
        else zone_key
    )
    f = fonts["md"]
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 9
    x0, y0 = cx - tw // 2 - pad, cy - th // 2 - pad
    return (x0, y0, x0 + tw + pad * 2, y0 + th + pad * 2)


def draw_mini_badge(draw, cx, cy, zone_key, zone_data, fonts):
    _, color = ZONE_COLORS[zone_key]
    text = (
        f"{zone_key} {zone_data['pct']}%"
        if zone_data.get("estimated", False)
        else zone_key
    )
    f = fonts["md"]
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 9
    x0, y0 = cx - tw // 2 - pad, cy - th // 2 - pad
    draw.rounded_rectangle(
        [x0, y0, x0 + tw + pad * 2, y0 + th + pad * 2],
        radius=6,
        fill="#FFFFFFCC",
        outline=color,
        width=2,
    )
    draw.text((cx - tw // 2, cy - th // 2), text, fill="#333333", font=f)


def choose_full_badge_spot(
    components,
    w,
    h,
    header_h,
    zone_key,
    zone_data,
    fonts,
    draw,
    placed_boxes,
    placed_centers,
):
    candidates = []
    for comp in components:
        _, box_w, box_h = measure_text_block(draw, badge_lines(zone_key, zone_data), fonts)
        cx, cy = anchor_badge_center(comp, w, h, header_h, box_w, box_h)
        rect = measure_full_badge_rect(draw, cx, cy, zone_key, zone_data, fonts)
        if any(rects_overlap(rect, other) for other in placed_boxes):
            continue
        candidates.append((comp["pts"], cx, cy, rect, comp["rx"]))

    if not candidates:
        return None

    if zone_key == "S":
        centered = [candidate for candidate in candidates if abs(candidate[1] - w / 2) < w * 0.12]
        if centered:
            candidates = centered

    if zone_key == "A":
        right_side = [c for c in candidates if c[1] > w / 2]
        if right_side:
            candidates = right_side

    if zone_key in ("A", "B"):
        partner = "B" if zone_key == "A" else "A"
        if partner in placed_centers:
            partner_cx, _ = placed_centers[partner]
            opposite = [c for c in candidates if (c[1] < w / 2) != (partner_cx < w / 2)]
            if opposite:
                candidates = opposite

    candidates.sort(key=lambda item: item[0], reverse=True)
    _, cx, cy, rect, _ = candidates[0]
    return cx, cy, rect


def group_zone_components(img, zones):
    grouped = {}
    for zone in ("SS", "S", "A", "B"):
        if zone not in zones:
            continue
        grouped[zone] = find_zone_components(img, zone)
    return grouped


def draw_info_panel(img_w, venue, fonts, mode):
    """Create a safe zone-only panel or an explicitly unverified estimate panel."""
    panel_h = 360 if mode == "estimates" else 190
    panel = Image.new("RGB", (img_w, panel_h), "#F8F9FA")
    draw = ImageDraw.Draw(panel)

    font_title = fonts["title"]
    font_md = fonts["md"]
    font_sm = fonts["sm"]

    y = 18
    title = f"{venue['name']}（{venue['name_zh']}）"
    draw.text((20, y), title, fill="#111111", font=font_title)
    y += 42

    if mode == "zones":
        meta = f"概略最大容量：約 {format_count(venue['total'])} 人  │  區域示意，不含票種人數"
        draw.text((20, y), meta, fill="#555555", font=font_sm)
        y += 40
        warning = "資料狀態：精確樓層容量與場地尺寸尚未完成官方來源查核"
        draw.text((20, y), warning, fill="#9A3412", font=font_md)
        note = "※SS／S／A／B 僅表示原始座位圖中的相對位置"
        draw.text((20, panel_h - 40), note, fill="#666666", font=font_sm)
        return panel

    meta = (
        f"UNVERIFIED ESTIMATE  │  總計：約 {format_count(venue['total'])} 人  │  "
        f"1F：{format_count(venue['floor_capacity'])} 人  │  "
        f"看台：{format_count(venue['stand_capacity'])} 人"
    )
    draw.text((20, y), meta, fill="#555555", font=font_sm)
    y += 38

    # Table header
    cols = [
        ("區域", 110),
        ("1F", 160),
        ("看台", 160),
        ("合計", 160),
        ("比例", 100),
        ("樓層", 220),
    ]
    x = 20
    for label, width in cols:
        draw.text((x, y), label, fill="#333333", font=font_md)
        x += width
    y += 36

    draw.line([(20, y), (img_w - 20, y)], fill="#CCCCCC", width=1)
    y += 12

    zone_order = ["SS", "S", "A", "B"]
    for zone_key in zone_order:
        if zone_key not in venue["zones"]:
            continue
        z = venue["zones"][zone_key]
        zone_name, color = ZONE_COLORS[zone_key]
        x = 20
        draw.ellipse([x, y + 6, x + 18, y + 24], fill=color)
        draw.text((x + 28, y), zone_name, fill="#222222", font=font_md)
        x += 110
        draw.text((x, y), format_count(z["floor_count"]), fill="#222222", font=font_md)
        x += 160
        draw.text((x, y), format_count(z["stand_count"]), fill="#222222", font=font_md)
        x += 160
        draw.text((x, y), format_count(z["count"]), fill="#222222", font=font_md)
        x += 160
        draw.text((x, y), f"{z['pct']}%", fill="#222222", font=font_md)
        x += 100
        draw.text((x, y), z["tier"], fill="#444444", font=font_sm)
        y += 40

    note = "※歷史推估：樓層容量未經驗證，非官方票種人數"
    draw.text((20, panel_h - 38), note, fill="#666666", font=font_sm)

    return panel


def validate_venue_metadata(venue):
    for field in ("capacity_status", "dimension_status"):
        if venue[field] not in VALID_CONFIDENCE_LEVELS:
            raise ValueError(f"{venue['name']}: invalid {field}={venue[field]}")
    if venue["floor_capacity"] + venue["stand_capacity"] > venue["total"]:
        raise ValueError(f"{venue['name']}: floor/stand capacity exceeds venue maximum")
    if venue["dimension_status"] == "confirmed" and not venue.get("dimension_scope"):
        raise ValueError(f"{venue['name']}: confirmed dimension lacks measurement scope")


def build_zone_only_data(zone_components):
    return {
        zone_key: {
            "estimated": False,
            "tier": "區域示意",
        }
        for zone_key in zone_components
    }


def annotate_venue(stem: str, venue: dict, mode: str, output_dir: Path):
    src = ORIGINAL_DIR / f"{stem}.jpg"
    if not src.exists():
        print(f"SKIP (not found): {src}")
        return

    validate_venue_metadata(venue)
    img = Image.open(src).convert("RGBA")
    w, h = img.size

    fonts = {
        "title": load_font(34, bold=True),
        "lg": load_font(30, bold=True),
        "md": load_font(26),
        "sm": load_font(22),
        "header": load_font(32, bold=True),
    }

    # Header bar
    header_h = 76
    header = Image.new("RGBA", (w, header_h), "#1A1A2E")
    hdraw = ImageDraw.Draw(header)
    if mode == "estimates":
        header_text = (
            f"{venue['name']}  │  UNVERIFIED  │  "
            f"總計約 {format_count(venue['total'])} 人"
        )
    else:
        header_text = f"{venue['name']}  │  區域示意（不含人數）"
    bbox = hdraw.textbbox((0, 0), header_text, font=fonts["header"])
    tw = bbox[2] - bbox[0]
    hdraw.text(((w - tw) // 2, 20), header_text, fill="#FFFFFF", font=fonts["header"])

    # Combine header + original
    combined = Image.new("RGBA", (w, header_h + h), (255, 255, 255, 255))
    combined.paste(header, (0, 0))
    combined.paste(img, (0, header_h))

    draw = ImageDraw.Draw(combined)

    zone_components = group_zone_components(img, venue["zones"])
    if not zone_components:
        print(f"SKIP (no labels detected): {src.name}")
        return
    venue = dict(venue)
    if mode == "estimates":
        venue["zones"] = calculate_zone_allocations(venue, zone_components)
    else:
        venue["zones"] = build_zone_only_data(zone_components)

    placed_boxes = []
    full_badge_centers = {}

    for zone_key in ("SS", "S", "A", "B"):
        if zone_key not in zone_components:
            continue
        spot = choose_full_badge_spot(
            zone_components[zone_key],
            w,
            h,
            header_h,
            zone_key,
            venue["zones"][zone_key],
            fonts,
            draw,
            placed_boxes,
            full_badge_centers,
        )
        if spot is None:
            continue
        cx, cy, rect = spot
        draw_zone_badge(draw, cx, cy, zone_key, venue["zones"][zone_key], fonts)
        placed_boxes.append(rect)
        full_badge_centers[zone_key] = (cx, cy)

    for zone_key in ("SS", "S", "A", "B"):
        if zone_key not in zone_components:
            continue
        for comp in zone_components[zone_key]:
            cx = int(comp["rx"] * w)
            cy = int(comp["ry"] * h) + header_h
            if zone_key in full_badge_centers:
                fx, fy = full_badge_centers[zone_key]
                if abs(cx - fx) < 40 and abs(cy - fy) < 40:
                    continue
            mini_rect = measure_mini_badge_rect(draw, cx, cy, zone_key, venue["zones"][zone_key], fonts)
            if any(rects_overlap(mini_rect, other, margin=8) for other in placed_boxes):
                continue
            draw_mini_badge(draw, cx, cy, zone_key, venue["zones"][zone_key], fonts)
            placed_boxes.append(mini_rect)

    # Bottom panel
    panel = draw_info_panel(w, venue, fonts, mode)
    panel_rgba = panel.convert("RGBA")

    final_h = header_h + h + panel.height
    final = Image.new("RGBA", (w, final_h), (255, 255, 255, 255))
    final.paste(combined, (0, 0))
    final.paste(panel_rgba, (0, header_h + h))

    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = "zones" if mode == "zones" else "unverified"
    out = output_dir / f"{stem}_{suffix}.jpg"
    final.convert("RGB").save(out, quality=95)
    print(f"OK: {out.name}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate zone-only maps or explicitly unverified estimates."
    )
    parser.add_argument(
        "--mode",
        choices=("zones", "estimates"),
        required=True,
        help="zones is safe; estimates uses deprecated unverified capacity assumptions",
    )
    parser.add_argument(
        "--allow-unverified-estimates",
        action="store_true",
        help="required acknowledgement for --mode estimates",
    )
    args = parser.parse_args()
    if args.mode == "estimates" and not args.allow_unverified_estimates:
        parser.error(
            "--mode estimates is blocked because capacity assumptions are unverified; "
            "pass --allow-unverified-estimates to acknowledge this"
        )
    return args


def main():
    args = parse_args()
    output_dir = ZONE_ONLY_DIR if args.mode == "zones" else UNVERIFIED_DIR
    if args.mode == "estimates":
        print("WARNING: generating deprecated, unverified estimates")
    for stem, venue in VENUES.items():
        annotate_venue(stem, venue, args.mode, output_dir)
    print("Done.")


if __name__ == "__main__":
    main()
