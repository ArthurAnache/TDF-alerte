#!/usr/bin/env python3
"""
Alerte TDF - surveille racecenter.letour.fr et envoie une notification push
(via ntfy.sh) dès que le groupe de tête du Tour de France est a <= 15 km
de l'arrivee.

Ne fait AUCUN appel a un LLM : ce script tourne seul, declenche par un cron
GitHub Actions, et n'appelle que racecenter.letour.fr + ntfy.sh.
"""

import datetime
import os
import re
import sys
import urllib.request

from playwright.sync_api import sync_playwright

THRESHOLD_KM = 125
STATE_FILE = "state/last_notified.txt"
RACE_CENTER_URL = "https://racecenter.letour.fr/en/"


DISTANCE_PATTERN = re.compile(r"([\d]+(?:\.[\d]+)?)\s*km remaining", re.IGNORECASE)


def get_distance_remaining() -> float | None:
    """Charge la page racecenter et extrait la distance restante (km) du
    groupe de tete, telle qu'affichee live sur la page (ex: '149 km remaining')."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(RACE_CENTER_URL, timeout=30000)
        try:
            # Element precis affichant la distance du groupe de tete.
            # Nom de classe observe sur le site au 07/07/2026 ; peut evoluer.
            page.wait_for_selector(".group__info__time", timeout=15000)
            text = page.locator(".group__info__time").first.inner_text()
        except Exception:
            # Repli : on cherche le motif dans tout le texte de la page.
            page.wait_for_timeout(3000)
            text = page.inner_text("body")
        browser.close()

    match = DISTANCE_PATTERN.search(text)
    if match:
        return float(match.group(1))
    return None


def already_notified_today() -> bool:
    if not os.path.exists(STATE_FILE):
        return False
    with open(STATE_FILE) as f:
        last = f.read().strip()
    return last == datetime.date.today().isoformat()


def mark_notified() -> None:
    os.makedirs("state", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(datetime.date.today().isoformat())


def send_notification(distance: float, topic: str) -> None:
    url = f"https://ntfy.sh/{topic}"
    message = f"Le Tour de France est a environ {distance:.0f} km de l'arrivee !"
    req = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        headers={
            "Title": "Alerte TDF - final approche".encode("utf-8"),
            "Priority": "high",
            "Tags": "bike,rotating_light",
        },
    )
    urllib.request.urlopen(req, timeout=15)


def main() -> None:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print("ERREUR: la variable d'environnement NTFY_TOPIC n'est pas definie.")
        sys.exit(1)

    distance = get_distance_remaining()
    print(f"[{datetime.datetime.now().isoformat()}] Distance restante detectee: {distance}")

    if distance is None:
        print("Aucune donnee de distance trouvee sur la page (course pas en cours ?).")
        return

    if distance <= THRESHOLD_KM:
        if already_notified_today():
            print("Deja notifie aujourd'hui, on ne renvoie pas de notification.")
        else:
            send_notification(distance, topic)
            mark_notified()
            print("Notification envoyee.")
    else:
        print("Distance encore superieure au seuil, pas de notification.")


if __name__ == "__main__":
    main()
