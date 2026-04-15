#!/bin/bash

# Script para configurar y ejecutar el semantic chunking en Linux/Mac

echo "========================================"
echo "Semantic Chunking Script Setup"
echo "========================================"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 no está instalado"
    exit 1
fi

echo ""
echo "[1] Ejecutando setup..."
python3 setup.py

echo ""
echo "[2] Instalando dependencias (si es necesario)..."
pip install -r requirements.txt

echo ""
echo "[3] Listo para ejecutar el script"
echo ""
echo "Para procesar las lecciones, ejecuta:"
echo "  python3 chunk_transcripts.py"
echo ""
