# Utilise une image Python légère
FROM python:3.10-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers
COPY . .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Expose le port Flask
EXPOSE 5000

# Démarrer Flask
CMD ["python", "app.py"]

