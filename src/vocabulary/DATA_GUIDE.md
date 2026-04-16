# Guia de datos — scripts, output/ y progress/

Este documento cubre los dos scripts del pipeline de clasificacion CEFR (`analyze_cefr_contextual.py` y `vocab_progress.py`) y los directorios de salida que generan (`output/` y `progress/`). Todos los archivos JSON usan UTF-8.

---

## Scripts

### analyze_cefr_contextual.py — Clasificador contextual CEFR

Clasifica cada palabra del alumno por nivel CEFR (A1–C2) usando Word Sense Disambiguation (WSD) con embeddings.

**Dependencias:** `sentence-transformers`, `nltk` (wordnet), `cefrpy`, `numpy`. Requiere el recurso CEFR-Annotated WordNet en `resources/cefr_wordnet/`.

**Uso:**
```bash
python analyze_cefr_contextual.py <input.json> [--window 5]
```

**Formatos de entrada soportados (auto-detectados):**
- **Deepgram:** `results.channels[0].alternatives[0].words[]` — transcripcion de audio con timestamps
- **Paragraphs:** `paragraphs[].sentences[].text` — texto organizado por parrafos tematicos con `paragraph_id` y `label`

**Algoritmo de clasificacion (por cada palabra):**

1. **Fast path:** Digitos → A1. Contracciones/interjecciones en whitelist → A1.
2. **WSD:** Busca synsets candidatos en WordNet. Embebe la ventana de contexto (+-N tokens) y las glosas de cada synset con `all-MiniLM-L6-v2`. Elige el synset con mayor similitud coseno (umbral minimo 0.15). Busca el nivel CEFR del sense_key en la CEFR-Annotated WordNet.
3. **Fallbacks (en orden):**
   - `lemma_fallback`: nivel CEFR minimo entre todos los senses del lema en WordNet
   - `cefrpy`: lookup directo por palabra (no contextual)
   - `UNKNOWN`: sin clasificacion posible

**Campo `source` en la salida** — indica que metodo se uso:

| source | Significado | Fiabilidad |
|--------|------------|------------|
| `wsd:synset_name` | WSD eligio un synset especifico | Alta — clasificacion contextual |
| `cefrpy` | Lookup por palabra sin contexto | Media — puede no reflejar el sentido usado |
| `whitelist` | Contraccion/interjeccion conocida (A1) | Alta |
| `lemma_fallback` | Nivel minimo entre todos los senses | Baja — conservador |
| `digit` | Numero → A1 | Alta |
| `no_synset` | Sin synsets en WordNet, cefrpy tampoco | N/A — probablemente nombre propio |
| `none` | Tiene synsets pero ninguno con nivel CEFR | Baja |

**Salida:** Escribe en `output/` (ver seccion siguiente).

---

### vocab_progress.py — Metricas de vocabulario y progreso

Post-procesamiento que agrega los resultados del clasificador contextual y calcula metricas de vocabulario por chunk, por leccion, y entre lecciones.

**Dependencias:** Solo libreria estandar de Python (json, math, collections, pathlib).

**Uso:**
```bash
python vocab_progress.py <Student-X> <lesson-Y>

# Ejemplo: procesar todas las lecciones de un alumno (en orden!)
python vocab_progress.py Student-1 lesson-1
python vocab_progress.py Student-1 lesson-2
python vocab_progress.py Student-1 lesson-3
```

**Lee de:** `output/Student-X_lesson-Y_*_contextual.json` + `progress/Student-X_history.json` (si existe)
**Escribe en:** `progress/Student-X_lesson-Y_progress.json` + `progress/Student-X_history.json`

**Algoritmo del score de vocabulario (`compute_vocab_level`):**

1. Agrupa todas las ocurrencias de cada palabra (lowercased)
2. Filtra: descarta `UNKNOWN`, confianza < 0.60, y nombres propios (heuristica: source `no_synset`/`none` + nivel C1/C2/UNKNOWN)
3. Calcula nivel representativo por palabra = **moda** de las ocurrencias (tie-break: nivel mas bajo)
4. Excluye **function words** (~60 palabras: determiners, pronouns, prepositions, auxiliaries, conjunctions)
5. Score = **media** de los niveles representativos de las content words unicas
6. Escala: A1=1.0, A2=2.0, B1=3.0, B2=4.0, C1=5.0, C2=6.0

**Scoring por chunk:**

El score se calcula primero por cada parrafo/chunk (usando los `total_words` de `paragraphs[]` para partir la lista plana de words). El score de la leccion es la **media** de los scores de todos los chunks.

**Tier 2 (comparacion entre lecciones):**

Solo disponible a partir de la segunda leccion procesada. Compara con el historial acumulado:
- Vocabulario nuevo (palabras no vistas antes)
- Retencion (palabras previas que reaparecen)
- Tendencia del score (regresion lineal)
- Crecimiento acumulado de vocabulario
- Migraciones de nivel (palabras que cambiaron de CEFR)

**Importante:** Las lecciones deben procesarse en **orden cronologico** porque tier2 compara con el historial acumulado hasta ese momento.

---

## output/ — Clasificacion contextual palabra por palabra

## output/ — Clasificacion contextual palabra por palabra

**Naming:** `Student-X_lesson-Y_contextual.json`

Cada archivo corresponde a una leccion completa de un estudiante. Contiene todas las palabras del alumno clasificadas por nivel CEFR.

### Estructura

```json
{
  "student": "Student-1",
  "lesson": "lesson-1",
  "words": [ ... ],
  "paragraphs": [ ... ],
  "stats": { ... }
}
```

### words[]

Lista plana de todas las palabras del alumno, en orden de aparicion.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `word` | string | La palabra tal como se dijo |
| `cefr_level` | string | Nivel CEFR asignado: `A1`, `A2`, `B1`, `B2`, `C1`, `C2` o `UNKNOWN` |
| `confidence` | float (0-1) | Confianza de la clasificacion |
| `source` | string | Metodo usado: `whitelist`, `wsd:synset_name`, `cefrpy`, `lemma_fallback`, `digit`, `no_synset`, `none` |

Ejemplo:
```json
{ "word": "Fine", "confidence": 1.0, "cefr_level": "A2", "source": "wsd:all_right.s.01" }
```

### paragraphs[]

Metadatos por parrafo/chunk (segmento tematico de la conversacion). Los `total_words` suman el total de `words[]`, asi que la lista plana de words se puede partir en chunks usando estos conteos secuencialmente.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `paragraph_id` | int | Identificador secuencial (1, 2, 3...) |
| `label` | string | Tema del chunk (ej. "Greetings and practicing relative clauses") |
| `total_words` | int | Numero de palabras en este chunk |
| `unique_words` | int | Palabras unicas en este chunk |
| `cefr_distribution` | object | Distribucion de niveles CEFR: `{ "A1": { "count": 191, "percent": 69.2 }, ... }` |

### stats

Estadisticas globales de la leccion (distribucion CEFR, fuentes de clasificacion, etc.).

---

## progress/ — Metricas de vocabulario y progreso

Dos tipos de archivo:

### Student-X_lesson-Y_progress.json — Metricas por leccion

Contiene metricas calculadas a partir del output contextual. Generado por `vocab_progress.py`.

```json
{
  "student": "Student-1",
  "lesson": "lesson-1",
  "segments_analyzed": 1,
  "flags": { ... },
  "tier1": { ... },
  "tier2": { ... },
  "vocabulary_snapshot": { ... }
}
```

#### flags

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `is_baseline` | bool | `true` si es la primera leccion procesada del alumno |
| `partial_lesson` | bool | `true` si se analizaron menos de la mitad de los segmentos esperados |
| `low_confidence` | bool | `true` si hay menos de 50 palabras totales |

#### tier1 — Metricas de la leccion

| Campo | Descripcion |
|-------|-------------|
| `vocab_level` | Score de vocabulario de la leccion (media de los scores de chunks) |
| `vocab_level.score` | Float 1.0–6.0 donde A1=1, A2=2, B1=3, B2=4, C1=5, C2=6 |
| `vocab_level.cefr_label` | Nivel CEFR equivalente al score (ej. "A2") |
| `vocab_level.content_words_scored` | Numero de content words usados para el calculo |
| `chunks[]` | **Score por chunk/parrafo** — cada uno con `paragraph_id`, `label`, y su propio `vocab_level` |
| `lexical_sophistication.lsi` | Proporcion de content words unicos en B2+ (0.0–1.0) |
| `lexical_diversity.ttr` | Type-Token Ratio |
| `lexical_diversity.root_ttr` | Indice de Guiraud (TTR normalizado) |
| `word_count` | `total_tokens`, `unique_words`, `unique_content_words` |
| `cefr_distribution` | Distribucion por nivel: `{ "A1": { "count": 1256, "percent": 67.67 }, ... }` |
| `source_distribution` | Porcentaje por metodo de clasificacion (`wsd`, `cefrpy`, `whitelist`, etc.) |
| `interesting_words[]` | Palabras B2+ con alta confianza, incluye `word`, `cefr_level`, `occurrence_count`, `context_quality` |

**chunks[] detalle:**
```json
{
  "paragraph_id": 1,
  "label": "Greetings and practicing relative clauses",
  "vocab_level": { "score": 2.3, "cefr_label": "A2", "content_words_scored": 95 }
}
```
El score de la leccion (`tier1.vocab_level.score`) es la **media** de los scores de todos los chunks.

#### tier2 — Comparacion entre lecciones (null en la primera leccion)

| Campo | Descripcion |
|-------|-------------|
| `comparison` | Tendencia del score: `scores[]`, `trend` (positive/negative/neutral), `trend_magnitude`, `vocab_level_change` |
| `new_vocabulary` | Palabras nuevas respecto a lecciones anteriores: `total_new`, `by_level`, `notable_new_words[]` |
| `retention` | Retencion de vocabulario previo: `overall_rate`, `retained_count`, `retained_advanced_words[]` |
| `active_vocabulary` | Crecimiento acumulado: `cumulative_unique[]`, `cumulative_b2_plus[]`, `growth_rate[]` |
| `level_migrations` | Palabras que cambiaron de nivel CEFR entre lecciones |

#### vocabulary_snapshot

Diccionario `{ word: { level, count, source } }` con todas las palabras clasificadas de la leccion. Se usa internamente para construir el historial.

---

### Student-X_history.json — Historial acumulado del alumno

Se actualiza cada vez que se procesa una leccion. Contiene el vocabulario acumulado a lo largo de todas las lecciones procesadas.

```json
{
  "student": "Student-1",
  "lessons_analyzed": ["lesson-1", "lesson-2", "lesson-3"],
  "cumulative_vocabulary": { ... },
  "lesson_scores": { ... }
}
```

| Campo | Descripcion |
|-------|-------------|
| `lessons_analyzed` | Lista ordenada de lecciones procesadas |
| `cumulative_vocabulary` | Diccionario con cada palabra vista: `first_seen`, `last_seen`, `lessons_present[]`, `levels_by_lesson`, `source_by_lesson` |
| `lesson_scores` | Score por leccion: `{ "lesson-1": { "vocab_level": 2.2, "lsi": 0.24, "root_ttr": 10.07, "unique_words": 434 } }` |

**Importante:** Las lecciones deben procesarse en orden cronologico porque tier2 compara con el historial acumulado hasta ese momento.

---

## Pipeline completo

```
Data/Student-1/lesson-1/*.json          (Deepgram transcripciones)
    o
Data/format.json                        (Paragraphs JSON)
    |
    v  analyze_cefr_contextual.py --window 5
    |
output/Student-1_lesson-1_contextual.json    (palabras + CEFR + paragraphs)
    |
    v  vocab_progress.py Student-1 lesson-1
    |
progress/Student-1_lesson-1_progress.json    (metricas tier1 + tier2)
progress/Student-1_history.json              (historial acumulado)
    |
    v  webapp (Next.js)
    |
Graficas de vocabulario en la web             (scores normalizados a 0-100)
```

1. **Input:** Transcripciones de audio (Deepgram) o texto dividido en parrafos bajo `Data/`
2. **`analyze_cefr_contextual.py`** clasifica cada palabra por CEFR → escribe en `output/`
3. **`vocab_progress.py`** calcula metricas por chunk, por leccion, y entre lecciones → escribe en `progress/`
4. **La webapp** lee de `progress/` para las graficas de vocabulario (scores normalizados a 0-100)

## Escala del score de vocabulario

El score bruto va de 1.0 (solo A1) a 6.0 (solo C2). La webapp lo normaliza a 0–100 con `(score / 6) * 100`:

| CEFR | Score | Sobre 100 |
|------|-------|-----------|
| A1 | 1.0 | 17 |
| A2 | 2.0 | 33 |
| B1 | 3.0 | 50 |
| B2 | 4.0 | 67 |
| C1 | 5.0 | 83 |
| C2 | 6.0 | 100 |
