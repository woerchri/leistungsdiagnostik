#!/bin/bash
# Desktop-Verknüpfung — öffnet Terminal im Werkzeugordner und startet Codex
cd ~/Leistungsdiagnostik/tool || { echo "Ordner ~/Leistungsdiagnostik/tool nicht gefunden."; read -r; exit 1; }
export PATH="$HOME/.local/bin:$PATH"
echo "Leistungsdiagnostik-Werkzeug bereit."
echo "Tippe /ld-report um einen Bericht zu erstellen."
codex
