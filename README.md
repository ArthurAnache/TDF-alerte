# Alerte TDF

Envoie une notification push sur ton téléphone dès que le groupe de tête du
Tour de France passe sous les 15 km de l'arrivée, pour ne pas manquer le
final de l'étape.

Fonctionne entièrement sans IA/LLM : un script Python (Playwright) lit la
distance restante affichée en direct sur racecenter.letour.fr, et un workflow
GitHub Actions le déclenche automatiquement toutes les 5 minutes pendant les
heures d'étape. Zéro coût, zéro token consommé en fonctionnement.

## 1. Installer l'app de notification (ntfy)

1. Installe l'app **ntfy** sur ton téléphone (disponible sur l'App Store et
   le Play Store, gratuite, open-source).
2. Dans l'app, abonne-toi (bouton "+" / "Subscribe to topic") au topic :

   ```
   tdf-alerte-5e9f5379
   ```

   (Ce nom est généré aléatoirement pour éviter que quelqu'un d'autre ne
   devine ton topic et t'envoie de fausses alertes. Tu peux le changer si tu
   préfères — il suffit de mettre à jour le secret GitHub à l'étape 3.)

## 2. Créer le dépôt GitHub

1. Crée un nouveau dépôt GitHub (public ou privé, peu importe).
2. Ajoute-y les fichiers de ce dossier : `monitor.py`, `requirements.txt`,
   `.gitignore`, `state/` (avec le fichier vide `.gitkeep`), et le dossier
   `.github/workflows/alerte-tdf.yml`.
3. Commit + push.

## 3. Configurer le secret NTFY_TOPIC

Dans le dépôt GitHub : **Settings → Secrets and variables → Actions → New
repository secret**.

- Nom : `NTFY_TOPIC`
- Valeur : `tdf-alerte-5e9f5379` (ou ton propre nom de topic)

## 4. Vérifier que les Actions sont actives

Dans l'onglet **Actions** du dépôt, assure-toi que les workflows sont
activés (GitHub les active par défaut, mais vérifie si le dépôt vient d'un
fork).

Le workflow se déclenche automatiquement du 4 au 26 juillet, entre 12h et
19h UTC (14h-21h à Paris), toutes les 5 minutes. Tu peux aussi le lancer
manuellement à tout moment via le bouton "Run workflow" dans l'onglet
Actions (utile pour tester).

## Comment ça marche

- `monitor.py` charge `racecenter.letour.fr`, lit la distance restante du
  groupe de tête, et si elle est ≤ 15 km, envoie une notification via
  `ntfy.sh` — une seule fois par jour (l'état est stocké dans
  `state/last_notified.txt` et committé automatiquement par le workflow).
- Aucun agent Claude n'est impliqué dans le fonctionnement courant : la
  logique de vérification et de notification tourne entièrement dans le
  script Python, exécuté par GitHub Actions.

## Limites connues

- L'affichage exact ("X km remaining") vient de la page publique
  racecenter.letour.fr. Si ASO change la structure de la page, le script
  peut cesser de fonctionner — il faudra alors ajuster le sélecteur CSS
  dans `monitor.py` (`.group__info__time`).
- Les dates/heures du cron sont calées sur le calendrier du Tour de France
  2026 (4-26 juillet). À mettre à jour chaque année.
- Les workflows planifiés GitHub Actions peuvent avoir quelques minutes de
  retard en cas de forte charge sur l'infrastructure GitHub — acceptable
  pour cet usage (la notif arrive à ~15 km, il reste du temps avant
  l'arrivée).
