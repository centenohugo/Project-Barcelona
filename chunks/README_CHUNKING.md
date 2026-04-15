# Semantic Chunking Script

Script para procesar transcripciones de lecciones y generar chunks semánticos con descripciones usando Claude API.

## Setup

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar API Key de Anthropic

**Opción A: Variable de entorno (recomendado)**
```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY = "tu-api-key-aqui"

# Windows (CMD)
set ANTHROPIC_API_KEY=tu-api-key-aqui

# Linux/Mac
export ANTHROPIC_API_KEY="tu-api-key-aqui"
```

**Opción B: Archivo `.env`**
Crea un archivo `.env` en la raíz del proyecto:
```
ANTHROPIC_API_KEY=tu-api-key-aqui
```

## Uso

### Ejecutar el script

```bash
python chunk_transcripts.py
```

### Configuración (en `chunk_transcripts.py`)

Puedes ajustar estos parámetros al inicio del script:

- **`N_CLUSTERS`**: Número fijo de chunks (ej: 5). Si es `None`, usa `SIMILARITY_THRESHOLD`
- **`SIMILARITY_THRESHOLD`**: Umbral de similitud para agrupar (-1 a 1). Valores más bajos = menos chunks
- **`MIN_SENTENCES_PER_CHUNK`**: Mínimo de oraciones por chunk antes de fusionar

## Estructura del Proyecto

```
Project-Barcelona/
├── Data/
│   ├── Student-1/
│   │   ├── lesson-1/
│   │   │   ├── 01.json
│   │   │   └── ...
│   │   └── lesson-2/
│   └── Student-2/
├── outputs/              # Se crea automáticamente
│   ├── Student-1_lesson-1_chunked.json
│   ├── Student-1_lesson-1_chunked.md
│   └── ...
├── chunk_transcripts.py
└── requirements.txt
```

## Salida

El script genera dos archivos por lección:

- **JSON**: `{Student}_{lesson}_chunked.json` - Datos estructurados con timestamps
- **Markdown**: `{Student}_{lesson}_chunked.md` - Formato legible para visualización

## Ejemplo de Salida JSON

```json
{
  "lesson": "lesson-1",
  "total_chunks": 5,
  "combined_duration_seconds": 123.45,
  "chunks": [
    {
      "chunk_id": 1,
      "description": "Introduction and greetings",
      "start_time": 2.32,
      "end_time": 16.39,
      "duration": 14.07,
      "sentences_count": 8,
      "full_text": "Hello? Hello? Fine. Fine. Fine. Thanks. Marcos, how are you? Very good.",
      "sentences": [...]
    }
  ]
}
```

## Solución de Problemas

### Error: "No student directories found"
- Verifica que la carpeta `Data/` existe y contiene `Student-*`

### Error de API Key
- Asegúrate de haber configurado `ANTHROPIC_API_KEY`
- Verifica que tienes créditos en tu cuenta de Anthropic

### Error de módulos faltantes
- Ejecuta: `pip install -r requirements.txt`

## Tiempo de Ejecución

El tiempo depende de:
- Número de lecciones
- Longitud de las transcripciones
- Llamadas a Claude API (puede ser lento)

Para pruebas rápidas, considera modificar `N_CLUSTERS` a un número menor.
