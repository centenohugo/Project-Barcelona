# 🚀 Guía Rápida - Semantic Chunking

## Inicio Rápido (3 pasos)

### Paso 1: Instalar dependencias

**Windows:**
```bash
setup.bat
```

**Linux/Mac:**
```bash
bash setup.sh
```

O manualmente:
```bash
pip install -r requirements.txt
```

### Paso 2: Configurar API Key

Obtén tu clave de [Anthropic Console](https://console.anthropic.com)

**Windows PowerShell:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

**Windows CMD:**
```cmd
set ANTHROPIC_API_KEY=sk-ant-...
```

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Paso 3: Ejecutar

```bash
python chunk_transcripts.py
```

## ¿Qué hace el script?

1. Lee todos los archivos JSON en `Data/Student-*/lesson-*/`
2. Extrae y agrupa las oraciones por similitud semántica
3. Genera descripciones de cada grupo usando Claude
4. Guarda los resultados en `outputs/`

## Salidas

Para cada lección se generan:
- **`.json`** - Datos estructurados con timestamps
- **`.md`** - Versión legible en Markdown

## Configuración

Edita `chunk_transcripts.py` línea 15-18:

```python
N_CLUSTERS = 5                    # Número de chunks (o None para automático)
SIMILARITY_THRESHOLD = -0.3       # Umbral de similitud (-1 a 1)
MIN_SENTENCES_PER_CHUNK = 2       # Mínimo de oraciones por chunk
```

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError` | Ejecuta `pip install -r requirements.txt` |
| `ANTHROPIC_API_KEY not found` | Configura la variable de entorno |
| `No student directories found` | Verifica que exista `Data/Student-*` |
| Error de API | Revisa tu saldo en Anthropic Console |

## Estructura de Archivos

```
Project-Barcelona/
├── Data/
│   └── Student-*/
│       └── lesson-*/
│           └── *.json
├── outputs/               ← Se crea automáticamente
│   ├── Student-1_lesson-1_chunked.json
│   ├── Student-1_lesson-1_chunked.md
│   └── ...
├── chunk_transcripts.py   ← Script principal
├── setup.py              ← Verificador de setup
├── requirements.txt      ← Dependencias
└── README_CHUNKING.md    ← Documentación completa
```

## Ejemplo de Resultado

**JSON:**
```json
{
  "lesson": "lesson-1",
  "total_chunks": 5,
  "chunks": [
    {
      "chunk_id": 1,
      "description": "Introduction and greetings",
      "start_time": 2.32,
      "duration": 14.07,
      "full_text": "Hello? Hello? Fine..."
    }
  ]
}
```

**Markdown:**
```markdown
# Lesson-1 - Semantic Chunks

## Chunk 1: Introduction and greetings

**Time**: 0:02 - 0:16 | **Sentences**: 8

Hello? Hello? Fine. Fine. Fine. Thanks. Marcos, how are you? Very good...

---
```

## Contacto / Soporte

Para reportar bugs o sugerencias, verifica `README_CHUNKING.md` para más detalles.
