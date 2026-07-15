#!/usr/bin/env python3
"""Generate docs/index.md — GitHub Pages YouTube seat-view search page."""

from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import quote_plus

from annotate_seatmaps import VENUES

WORKDIR = Path(__file__).parent
ORIGINAL_DIR = WORKDIR / "original"
DOCS_DIR = WORKDIR / "docs"
DOCS_ORIGINAL = DOCS_DIR / "original"
OUTPUT = DOCS_DIR / "index.md"

# Tour order aligned with sakanaction_2027_venue_factcheck.md
TOUR_ORDER = [
    "seatmap_lala",
    "seatmap_kitaeru",
    "seatmap_kobe",
    "seatmap_portmesse",
    "seatmap_anabuki",
    "seatmap_zevioarena",
    "seatmap_sundom",
    "seatmap_marinmesse",
    "seatmap_hiroshima",
]

# Second search aliases for venues with multiple common names
ALT_NAMES: dict[str, str] = {
    "seatmap_kitaeru": "北海道立総合体育センター",
    "seatmap_kobe": "神戸ワールド記念ホール",
    "seatmap_hiroshima": "広島県立総合体育館",
}

ZONE_ORDER = ("SS", "S", "A", "B")


def youtube_search_url(query: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"


def search_rows(key: str, venue: dict) -> list[tuple[str, str]]:
    """Return list of (label, query) for one venue."""
    name = venue["name"]
    rows: list[tuple[str, str]] = [
        ("全館概覽", f"{name} ライブ 客席 視野"),
    ]

    alt = ALT_NAMES.get(key)
    if alt:
        rows.append(("別名搜尋", f"{alt} ライブ 視野"))

    for zone in ZONE_ORDER:
        if zone in venue["zones"]:
            rows.append((f"{zone}席", f"{name} {zone}席 見え方"))

    if venue.get("stand_capacity", 0) > 0:
        rows.append(("1F 地板席", f"{name} アリーナ席 視野 POV"))
        rows.append(("看台", f"{name} スタンド 見え方"))
    else:
        # Port Messe style: flat floor only
        rows.append(("前方／後方", f"{name} 前方 後方 見え方"))

    return rows


def slug_anchor(name: str) -> str:
    """GitHub / kramdown style heading anchor (spaces → -, ASCII lowercased)."""
    return name.replace(" ", "-").lower()


def build_markdown() -> str:
    lines: list[str] = [
        "# 2027透明｜場內視角 YouTube 搜尋",
        "",
        "SAKANAQUARIUM 2026-2027「透明」巡演場館的**場內視角（POV）**參考搜尋頁。",
        "點擊連結後，在 YouTube 結果中挑選標明座位區域的粉絲／觀眾影片。",
        "",
        "## 使用方式",
        "",
        "1. 展開下方場館，點擊對應票種或樓層的搜尋連結。",
        "2. 篩選標題含「見え方」「視野」「POV」「席から」等關鍵字的影片。",
        "3. 依頁尾**檢查清單**核對後再收錄為參考資料。",
        "",
        "## 可信度聲明",
        "",
        "- YouTube 粉絲／觀眾影片僅屬**概略可用**：適合了解距離感、高度與大致視野。",
        "- **不可**替代官方座席表、售票配置或 technical rider（見 [`venues_Dataset.md`](../venues_Dataset.md)）。",
        "- 2027 本巡演多數場次尚未舉行；搜尋結果多為同場館**其他演唱會**，舞台配置可能不同。",
        "- SS／S／A／B 為票種標籤，各巡演分區未必一致，標題標記也常有誤差。",
        "",
        "## 目錄（巡演順序）",
        "",
    ]

    for i, key in enumerate(TOUR_ORDER, start=1):
        venue = VENUES[key]
        title = f"{i}. {venue['name']}（{venue['name_zh']}）"
        lines.append(f"- [{title}](#{i}-{slug_anchor(venue['name'])})")

    lines.extend(["", "---", ""])

    for i, key in enumerate(TOUR_ORDER, start=1):
        venue = VENUES[key]
        name = venue["name"]
        name_zh = venue["name_zh"]
        original_img = f"original/{key}.jpg"

        lines.append(f"## {i}. {name}")
        lines.append("")
        lines.append(f"**{name_zh}**")
        lines.append("")
        lines.append(f"**原始座席圖**（[`{key}.jpg`]({original_img})）")
        lines.append("")
        lines.append(f"![{name} 原始座席圖]({original_img})")
        lines.append("")
        lines.append("<details open>")
        lines.append("<summary>展開／收合搜尋連結</summary>")
        lines.append("")
        lines.append("| 類型 | 關鍵字 | 連結 |")
        lines.append("|---|---|---|")

        for label, query in search_rows(key, venue):
            url = youtube_search_url(query)
            lines.append(f"| {label} | `{query}` | [YouTube 搜尋]({url}) |")

        if venue.get("stand_capacity", 0) == 0:
            lines.append("")
            lines.append("> 此場為單層平面配置（無常設高架看台）；票種僅 SS／S／A。")

        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## 影片篩選檢查清單",
            "",
            "收錄或引用某支影片前，請確認：",
            "",
            "- [ ] 場館名稱正確（含 A館／第一展示館等）",
            "- [ ] 票種區是否明確（SS／S／A／B）",
            "- [ ] 樓層（1F アリーナ席 vs スタンド）",
            "- [ ] 舞台配置（中央舞台／端舞台）",
            "- [ ] 拍攝日期與藝人（與 2027 配置可能不同）",
            "- [ ] 是否為相對固定的客席視角（非大量剪輯片段）",
            "",
            "## 相關文件",
            "",
            "- [場館資料分級](../venues_Dataset.md)（`venues_Dataset.md`）",
            "- [補查清單](../venue_research_backlog.md)（`venue_research_backlog.md`）",
            "- [查證報告](../sakanaction_2027_venue_factcheck.md)（`sakanaction_2027_venue_factcheck.md`）",
            "",
            "---",
            "",
            "*本頁由 `build_venue_youtube_search.py` 自動產生；修改場館資料後請重新執行腳本。*",
            "",
        ]
    )

    return "\n".join(lines)


def sync_images() -> None:
    """Copy original seat maps into docs/ for GitHub Pages."""
    DOCS_ORIGINAL.mkdir(parents=True, exist_ok=True)

    for key in TOUR_ORDER:
        src_orig = ORIGINAL_DIR / f"{key}.jpg"
        if src_orig.is_file():
            shutil.copy2(src_orig, DOCS_ORIGINAL / f"{key}.jpg")
        else:
            print(f"warning: missing {src_orig}")


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    sync_images()
    text = build_markdown()
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(WORKDIR)} ({len(text)} bytes)")


if __name__ == "__main__":
    main()
