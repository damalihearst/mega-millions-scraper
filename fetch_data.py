import urllib.request
import re
import csv
import os
from datetime import datetime


URL = "https://www.molottery.com/mega-millions/number-frequencies"


def fetch_page(url):
    """Fetch the HTML content of the page."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


def parse_frequency_table(html):
    """
    Parse the frequency table from the HTML.
    Targets: <table class="table table_game table_game_1-3 table_highlight-first">
    Returns a list of dicts.
    """
    # Locate the target table
    table_pattern = re.compile(
        r'<table\s+class="table table_game table_game_1-3 table_highlight-first">'
        r'(.*?)</table>',
        re.DOTALL,
    )
    table_match = table_pattern.search(html)
    if not table_match:
        raise ValueError("Could not find the frequency table on the page.")

    table_html = table_match.group(1)

    # Find all data rows (skip header rows and the footer row with colspan)
    row_pattern = re.compile(r"<tr>(.*?)</tr>", re.DOTALL)
    td_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)

    rows = row_pattern.findall(table_html)
    data = []

    for row in rows:
        # Skip rows that contain <th> or colspan (header/footer)
        if "<th" in row or "colspan" in row:
            continue

        cells = td_pattern.findall(row)
        if len(cells) < 3:
            continue

        # Clean cell values: strip &nbsp; and whitespace
        cleaned = [
            cell.replace("&nbsp;", "").replace("\n", "").replace("\r", "").strip()
            for cell in cells
        ]

        number = cleaned[0]
        white_times = cleaned[1]
        white_pct = cleaned[2].replace("%", "")

        mega_times = ""
        mega_pct = ""
        if len(cleaned) >= 5 and cleaned[3] != "" and cleaned[4] != "":
            mega_times = cleaned[3]
            mega_pct = cleaned[4].replace("%", "")

        data.append(
            {
                "number": int(number),
                "white_ball_times_drawn": int(white_times),
                "white_ball_pct": float(white_pct),
                "mega_ball_times_drawn": int(mega_times) if mega_times else None,
                "mega_ball_pct": float(mega_pct) if mega_pct else None,
            }
        )

    return data


def save_to_csv(data, filepath):
    """Save the parsed data to a CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    fieldnames = [
        "number",
        "white_ball_times_drawn",
        "white_ball_pct",
        "mega_ball_times_drawn",
        "mega_ball_pct",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def main():
    print(f"[{datetime.now().isoformat()}] Fetching data from {URL}")
    html = fetch_page(URL)

    print("Parsing frequency table...")
    data = parse_frequency_table(html)
    print(f"Found {len(data)} rows of data.")

    output_path = os.path.join("data", "mega-millions.csv")
    save_to_csv(data, output_path)
    print(f"Data saved to {output_path}")


if __name__ == "__main__":
    main()

