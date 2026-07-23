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


def send_discord(webhook, events):
    if not events:
        return

    embeds = []

    for event in events:
        embeds.append({
            "title": f"🚩 {event['title']}",
            "url": event["url"],

            "thumbnail": {
                "url": "https://ctftime.org/static/images/ct/logo.svg"
            },

            "fields": [
                {
                    "name": "📅 Début",
                    "value": event["start"],
                    "inline": False
                },
                {
                    "name": "⏱ Durée",
                    "value": str(event["duration"]),
                    "inline": False
                },
                {
                    "name": "🏆 Plateforme",
                    "value": "CTFTime",
                    "inline": False
                },
                {
                    "name": "🔗 Lien",
                    "value": event["url"],
                    "inline": False
                }
            ],

            "footer": {
                "text": "CTFTime Bot • Nouveaux CTF",
                "icon_url": "https://ctftime.org/static/images/ct/logo.svg"
            },

            "color": 16711680
        })

    payload = {
        "content": "🚩 **Nouveaux CTF disponibles**",
        "username": "ΠΡΙΜΕ BOT",
        "avatar_url": "https://raw.githubusercontent.com/lux/ctftime-discord-bot/main/assets/bot-icon.png",
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
