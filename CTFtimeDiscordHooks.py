#!/usr/bin/env python3

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests


CTFTIME_API = "https://ctftime.org/api/v1/events/"


def load_cache(cache_dir):
    cache_file = Path(cache_dir) / "ctftime.json"

    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    return []


def save_cache(cache_dir, data):
    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    cache_file = Path(cache_dir) / "ctftime.json"

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fetch_ctfs(days):
    now = datetime.now(timezone.utc).timestamp()

    params = {
        "limit": 50
    }

    headers = {
        "User-Agent": "CTFtimeDiscordBot/1.0 (GitHub Actions)"
    }

    response = requests.get(
        CTFTIME_API,
        params=params,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    events = response.json()

    upcoming = []

    for event in events:
        if event.get("start") is None:
            continue

        start = datetime.fromisoformat(
            event["start"].replace("Z", "+00:00")
        ).timestamp()

        if start <= now + days * 86400:
            upcoming.append({
                "id": event["id"],
                "title": event["title"],
                "url": event["ctftime_url"],
                "start": event["start"],
                "duration": event.get("duration")
            })

    return upcoming


def format_date(date):
    dt = datetime.fromisoformat(
        date.replace("Z", "+00:00")
    )

    return dt.strftime(
        "%A %d-%m-%Y à %HH%M UTC"
    )


def format_duration(duration):
    if not duration:
        return "Non défini"

    days = duration.get("days", 0)
    hours = duration.get("hours", 0)

    parts = []

    if days:
        parts.append(f"{days} jour{'s' if days > 1 else ''}")

    if hours:
        parts.append(f"{hours} heure{'s' if hours > 1 else ''}")

    if not parts:
        return "Moins d'une heure"

    return " et ".join(parts)


def send_discord(webhook, events):
    if not events:
        return

    embeds = []

    for event in events:

        embeds.append({
            "title": f"🚩 {event['title']}",

            "url": event["url"],

            "description": (
                "🏆 **Plateforme :** CTFTime\n"
                "🔗 **Lien :** "
                f"[Voir le challenge]({event['url']})"
            ),

            "fields": [
                {
                    "name": "📅 Début",
                    "value": format_date(event["start"]),
                    "inline": False
                },
                {
                    "name": "⏱ Durée",
                    "value": format_duration(event["duration"]),
                    "inline": False
                }
            ],

            "thumbnail": {
                "url": "https://github.com/whitexudan15/ctftime-discord-bot/blob/main/assets/prime-bot.png?raw=true"
            },

            "footer": {
                "text": "ΠΡΙΜΕ BOT • NEWS CTF",
                "icon_url": "https://github.com/whitexudan15/ctftime-discord-bot/blob/main/assets/prime-bot.png?raw=true"
            },

            "color": 16711680
        })

    payload = {
        "content": "🚩 **NEWS CTF**",
        "username": "ΠΡΙΜΕ BOT",
        "avatar_url": "https://github.com/whitexudan15/ctftime-discord-bot/blob/main/assets/prime-bot.png?raw=true",
        "embeds": embeds
    }

    response = requests.post(
        webhook,
        json=payload,
        timeout=20
    )

    response.raise_for_status()


def main():

    parser = argparse.ArgumentParser(
        description="CTFTime Discord notifier"
    )

    parser.add_argument(
        "-w",
        "--webhook",
        required=True,
        help="Discord webhook URL"
    )

    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=10,
        help="Nombre de jours à surveiller"
    )

    parser.add_argument(
        "-c",
        "--cache",
        default="ctftime_cache",
        help="Répertoire cache"
    )

    args = parser.parse_args()


    old_events = load_cache(args.cache)

    current_events = fetch_ctfs(args.days)


    old_ids = {
        event["id"]
        for event in old_events
    }


    new_events = [
        event
        for event in current_events
        if event["id"] not in old_ids
    ]


    if new_events:
        send_discord(
            args.webhook,
            new_events
        )

        print(
            f"{len(new_events)} ✅"
        )

    else:
        print(
            "❌"
        )


    save_cache(
        args.cache,
        current_events
    )


if __name__ == "__main__":
    main()
