# Documentation A-sistemo

Bienvenue sur A-sistemo — commandes de gestion système pour A.

## Démarrage Rapide

### Installation

```bash
pip install A-sistemo
```

Ou depuis les sources:

```bash
git clone https://github.com/Ron-RONZZ-org/A-sistemo.git
cd A-sistemo
poetry install
```

### Utilisation de Base

```bash
A sistemo --help           # Afficher l'aide
A sistemo help            # Afficher l'aide
A sistemo ls             # Liste des sous-commandes
```

---

## Commandes

A-sistemo fournit des commandes de gestion système:

| Commande | Description |
|---------|-------------|
| `info` | Informations système |
| `wifi` | Gestion Wi-Fi |
| `bluhdento` | Gestion Bluetooth |
| `usb` | Appareils USB |
| `disko` | Appareils disque |
| `particio` | Gestion des partitions |
| `rubo` | Gestion de la corbeille |
| `selo-aliaso` | Gestion des alias Bash |
| `selo-funkcio` | Gestion des fonctions Bash |

### Informations Système

```bash
A sistemo info      # Afficher les informations système
```

### Wi-Fi

```bash
A sistemo wifi ls           # Liste des réseaux Wi-Fi
A sistemo wifi konekti SSID  # Se connecter au réseau
```

### Bluetooth

```bash
A sistemo bluhdento ls        # Liste des appareils Bluetooth
```

### USB

```bash
A sistemo usb ls           # Liste des appareils USB
```

### Disques

```bash
A sistemo disko ls        # Liste des appareils disque
```

### Partitions

```bash
A sistemo particio ls      # Liste des partitions
```

### Corbeille

```bash
A sistemo rubo ls          # Liste la corbeille
A sistemo ruboelton       # Vider la corbeille
```

### Alias Bash

```bash
A sistemo selo-aliaso ls        # Liste les alias
```

### Fonctions Bash

```bash
A sistemo selo-funkcio ls          # Liste les fonctions
A sistemo selo-funkcio aldoni FICHIER # Ajouter des fonctions depuis un fichier
A sistemo selo-funkcio vidi UID    # Voir une fonction
A sistemo selo-funkcio modifi UID  # Modifier une fonction
A sistemo selo-funkcio forigi UID  # Supprimer une fonction
A sistemo selo-funkcio serci Q     # Rechercher des fonctions
```

Prend en charge la mise à jour automatique des doublons (--jes pour ignorer la confirmation).

---

## Architecture

A-sistemo a une architecture simple en deux couches:

```
CLI Layer (Typer)
Service Layer
```

---

## Dépendances

A-sistemo dépend de A-core.

---

## Licence

GPL-3.0-only