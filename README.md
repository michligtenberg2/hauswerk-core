# 🛠️ Hauswerk Core

**Hauswerk Core** is een modulaire Python GUI-applicatie voor het laden, beheren en installeren van audiovisuele plugins.

---

## ✅ Features

- 🔌 Dynamische plugin loader (uit `/plugins/`)
- 📦 Installeer plugins via ZIP-bestanden (drag & drop of knop)
- 🛍️ Plugin Store met live download vanuit GitHub (official & unofficial downloads, zie hauswerk-plugins;)
- 🎨 Licht/donker thema via `.qss`

---

## 📦 Vereisten

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) geïnstalleerd en in je `$PATH`
- Pip packages:

```bash
pip install -r requirements.txt
```

---

## 📂 Mappenstructuur

```
hauswerk_core/
├── __main__.py
├── core/
│   ├── settings.py
│   └── style.py
├── widgets/
│   ├── standard_tool_layout.py
│   └── pluginstoregrid.py
├── resources/
│   └── themes/
│       ├── dark.qss
│       └── light.qss
└── plugins/
    └── (jouw plugins hier)
```

---

## 🔌 Plugin toevoegen

Plaats een map in `/plugins/` met daarin:

- `main.py`
- `metadata.json`:

```json
{
  "name": "Collage",
  "entry": "main.py",
  "class": "CollageWidget",
  "icon": "icon.png"
}
```

---

## 🌐 Plugin Store (live)

De store laadt plugins van:

```
https://github.com/michligtenberg2/hauswerk-plugins/blob/main/plugins.json
```

Plugins worden automatisch getoond in de GUI en zijn met één klik te installeren.

---

© 2025 M. Ligtenberg — Deel van het Hauswerk ecosysteem.
