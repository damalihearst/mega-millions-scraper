import urllib.request
import re
import csv
import os
import json
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
    Returns a list of dicts with keys:
        number, white_ball_times_drawn, white_ball_pct,
        mega_ball_times_drawn, mega_ball_pct
    """
    # Locate the target table
    table_pattern = re.compile(
        r'<table\s+class="table table_game table_game_1-3 table_highlight-first">\'
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


def analyze_frequencies(data):
    """
    Determine the top 5 and bottom 5 most/least common numbers
    for both white balls and mega balls.
    Returns a dict with the analysis results.
    """
    # White ball analysis (all 70 numbers)
    white_sorted = sorted(data, key=lambda x: x["white_ball_times_drawn"], reverse=True)
    top_5_white = [
        {"number": row["number"], "times_drawn": row["white_ball_times_drawn"], "pct": row["white_ball_pct"]}
        for row in white_sorted[:5]
    ]
    bottom_5_white = [
        {"number": row["number"], "times_drawn": row["white_ball_times_drawn"], "pct": row["white_ball_pct"]}
        for row in white_sorted[-5:]
    ]

    # Mega ball analysis (only numbers 1-25 have mega ball data)
    mega_data = [row for row in data if row["mega_ball_times_drawn"] is not None]
    mega_sorted = sorted(mega_data, key=lambda x: x["mega_ball_times_drawn"], reverse=True)
    top_5_mega = [
        {"number": row["number"], "times_drawn": row["mega_ball_times_drawn"], "pct": row["mega_ball_pct"]}
        for row in mega_sorted[:5]
    ]
    bottom_5_mega = [
        {"number": row["number"], "times_drawn": row["mega_ball_times_drawn"], "pct": row["mega_ball_pct"]}
        for row in mega_sorted[-5:]
    ]

    return {
        "white_ball": {
            "top_5_most_common": top_5_white,
            "top_5_least_common": bottom_5_white,
        },
        "mega_ball": {
            "top_5_most_common": top_5_mega,
            "top_5_least_common": bottom_5_mega,
        },
    }


def save_analysis(analysis, filepath):
    """Save the analysis results to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)


def print_analysis(analysis):
    """Print a formatted summary of the analysis."""
    print("\n" + "=" * 60)
    print("MEGA MILLIONS NUMBER FREQUENCY ANALYSIS")
    print("=" * 60)

    print("\n--- TOP 5 MOST COMMON WHITE BALL NUMBERS ---")
    for i, item in enumerate(analysis["white_ball"]["top_5_most_common"], 1):
        print(f"  {i}. Ball #{item['number']:>2} - drawn {item['times_drawn']} times ({item['pct']}%)")

    print("\n--- TOP 5 LEAST COMMON WHITE BALL NUMBERS ---")
    for i, item in enumerate(analysis["white_ball"]["top_5_least_common"], 1):
        print(f"  {i}. Ball #{item['number']:>2} - drawn {item['times_drawn']} times ({item['pct']}%)")

    print("\n--- TOP 5 MOST COMMON MEGA BALL NUMBERS ---")
    for i, item in enumerate(analysis["mega_ball"]["top_5_most_common"], 1):
        print(f"  {i}. Ball #{item['number']:>2} - drawn {item['times_drawn']} times ({item['pct']}%)")

    print("\n--- TOP 5 LEAST COMMON MEGA BALL NUMBERS ---")
    for i, item in enumerate(analysis["mega_ball"]["top_5_least_common"], 1):
        print(f"  {i}. Ball #{item['number']:>2} - drawn {item['times_drawn']} times ({item['pct']}%)")

    print("\n" + "=" * 60)


def main():
    print(f"[{datetime.now().isoformat()}] Fetching data from {URL}")
    html = fetch_page(URL)

    print("Parsing frequency table...")
    data = parse_frequency_table(html)
    print(f"Found {len(data)} rows of data.")

    # Save raw data to CSV
    csv_path = os.path.join("data", "mega-millions.csv")
    save_to_csv(data, csv_path)
    print(f"Data saved to {csv_path}")

    # Analyze and save top/bottom 5
    analysis = analyze_frequencies(data)
    analysis_path = os.path.join("data", "analysis.json")
    save_analysis(analysis, analysis_path)
    print(f"Analysis saved to {analysis_path}")

    # Print summary
    print_analysis(analysis)


if __name__ == "__main__":
    main()
