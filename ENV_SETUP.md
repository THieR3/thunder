# Configuration & variables d'environnement

Copiez `.env.example` en `.env` puis remplissez les variables suivantes :

- `ANTHROPIC_API_KEY` : (optionnel) clé API pour le mode IA (Claude).
- `FIREBASE_CREDENTIALS` : chemin vers le fichier JSON de compte de service Firebase (ex. `tlp.1/serviceAccountKey.json`).

Ne commitez jamais le fichier `.env` ni votre fichier de clé Firebase dans le dépôt public.

Étapes rapides pour exécuter localement :

```bash
# Depuis la racine du projet (venv activé)
d:/thunder/venv/Scripts/python.exe app.py
```

Placez la clé de service Firebase (le fichier JSON) à l'emplacement indiqué par `FIREBASE_CREDENTIALS` dans `.env`.

Si vous préférez que j'insère cette section dans `tlp.1/README.md`, je peux le faire maintenant.
