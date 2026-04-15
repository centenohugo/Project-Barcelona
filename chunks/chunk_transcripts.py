#!/usr/bin/env python3
"""
Semantic chunking for lesson transcripts.
Combines multiple JSON transcript files, performs semantic clustering,
and generates topic descriptions using Claude API.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
from sentence_transformers import SentenceTransformer
from anthropic import Anthropic

# Configuration
REPO_ROOT = Path(__file__).parent
DATA_PATH = REPO_ROOT / "Data"  # Base path to Student-X folders
OUTPUT_DIR = REPO_ROOT / "outputs"  # Directory to save all processed outputs
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = -0.3  # Threshold for grouping similar sentences. Try reducing this value to get fewer chunks.
N_CLUSTERS = 5  # Set to an integer to get a fixed number of clusters, or None to use SIMILARITY_THRESHOLD.
MIN_SENTENCES_PER_CHUNK = 2  # Minimum sentences before merging small chunks

# Initialize clients and models
client = Anthropic()
embedder = SentenceTransformer(EMBEDDING_MODEL)


def load_json_files(lesson_path: Path) -> List[Dict]:
    """Load and combine transcripts from all JSON files in order."""
    json_files = sorted(lesson_path.glob("*.json"))
    print(f"Found {len(json_files)} JSON files in {lesson_path.name}")

    combined_sentences = []

    for json_file in json_files:
        print(f"  Loading {json_file.name}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract sentences from the JSON structure
        # The transcripts have sentence objects in:
        # results.channels[0].alternatives[0].paragraphs.paragraphs[*].sentences[]
        try:
            channels = data.get("results", {}).get("channels", [])
            if channels:
                alternatives = channels[0].get("alternatives", [])
                if alternatives:
                    paragraphs_obj = alternatives[0].get("paragraphs", {})
                    paragraphs_list = paragraphs_obj.get("paragraphs", [])
                    for para in paragraphs_list:
                        sentences = para.get("sentences", [])
                        for sent in sentences:
                            combined_sentences.append(sent)
        except (KeyError, IndexError, TypeError) as e:
            print(f"  ⚠ Error extracting sentences from {json_file.name}: {e}")

    print(f"  Total sentences extracted: {len(combined_sentences)}")
    return combined_sentences


def generate_embeddings(sentences: List[Dict]) -> Tuple[np.ndarray, List[str]]:
    """Generate embeddings for all sentences."""
    texts = [sent["text"] for sent in sentences]
    print(f"Generating embeddings for {len(texts)} sentences...")
    embeddings = embedder.encode(texts, show_progress_bar=True)
    return embeddings, texts


def cluster_sentences(embeddings: np.ndarray, sentences: List[Dict]) -> List[List[int]]:
    """Cluster sentences by semantic similarity using hierarchical clustering."""
    print("Clustering sentences by semantic similarity...")

    # Compute distance matrix
    distances = cosine_distances(embeddings)

    # Use hierarchical clustering with a distance threshold or fixed number of clusters
    if N_CLUSTERS is not None:
        if N_CLUSTERS > len(embeddings):
            print(f"Warning: N_CLUSTERS ({N_CLUSTERS}) is greater than the number of sentences ({len(embeddings)}). Setting N_CLUSTERS to number of sentences.")
            n_clusters_val = len(embeddings)
        else:
            n_clusters_val = N_CLUSTERS
        clusterer = AgglomerativeClustering(n_clusters=n_clusters_val, linkage='average')
        print(f"Clustering into a fixed number of {n_clusters_val} clusters.")
    else:
        clusterer = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=1 - SIMILARITY_THRESHOLD,  # Convert similarity to distance
            linkage='average'
        )
        print(f"Clustering with similarity threshold: {SIMILARITY_THRESHOLD}")

    labels = clusterer.fit_predict(embeddings)

    # Group sentence indices by cluster
    num_clusters = len(np.unique(labels))
    clusters = [[] for _ in range(num_clusters)]
    for idx, label in enumerate(labels):
        clusters[label].append(idx)

    # Keep clusters in original order
    clusters.sort(key=lambda c: c[0])

    print(f"Created {len(clusters)} semantic chunks")
    return clusters


def merge_small_clusters(clusters: List[List[int]], min_size: int = MIN_SENTENCES_PER_CHUNK) -> List[List[int]]:
    """Merge clusters smaller than min_size with adjacent clusters."""
    # Only merge if not using a fixed N_CLUSTERS, as fixed clusters should already be of appropriate size or handle small ones differently.
    if N_CLUSTERS is not None:
        print("Skipping merging small clusters as N_CLUSTERS is specified.")
        return clusters

    merged = []
    i = 0
    while i < len(clusters):
        current = clusters[i]

        # If too small, merge with next cluster
        while len(current) < min_size and i + 1 < len(clusters):
            current.extend(clusters[i + 1])
            i += 1

        merged.append(sorted(current))
        i += 1

    return merged


def generate_chunk_descriptions(chunks: List[Dict], texts: List[str]) -> List[str]:
    """Generate descriptions for each chunk using Claude API."""
    print("Generating descriptions with Claude API...")
    descriptions = []

    for i, chunk in enumerate(chunks):
        # Combine text from all sentences in this chunk
        chunk_text = " ".join(texts[idx] for idx in chunk["sentence_indices"])

        # Limit text to first 2000 characters to keep API calls reasonable
        chunk_text_preview = chunk_text[:2000]

        print(f"  Generating description for chunk {i + 1}/{len(chunks)}...")

        # Call Claude to generate a short description
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": f"Please provide a very short (1 sentence max) topic description for this transcript segment:\n\n{chunk_text_preview}"
                }
            ]
        )

        description = message.content[0].text.strip()
        descriptions.append(description)

    return descriptions


def create_chunks(sentences: List[Dict], clusters: List[List[int]], texts: List[str]) -> List[Dict]:
    """Create chunk objects with timing and metadata."""
    chunks = []

    for cluster in clusters:
        # Get all sentences in this cluster
        cluster_sentences = [sentences[idx] for idx in cluster]

        # Calculate timing
        start_time = min(sent.get("start", 0) for sent in cluster_sentences)
        end_time = max(sent.get("end", 0) for sent in cluster_sentences)

        # Combine text
        full_text = " ".join(sent["text"] for sent in cluster_sentences)

        chunk = {
            "sentence_indices": cluster,
            "sentences": cluster_sentences,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time,
            "sentences_count": len(cluster_sentences),
            "full_text": full_text,
        }
        chunks.append(chunk)

    return chunks


def format_time(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


def save_json_output(chunks: List[Dict], descriptions: List[str], output_path: Path) -> None:
    """Save chunks to JSON format."""
    output_data = {
        "lesson": output_path.stem.replace("_chunked", ""),  # Extract lesson name from filename
        "total_chunks": len(chunks),
        "combined_duration_seconds": sum(c["duration"] for c in chunks),
        "chunks": []
    }

    for i, chunk in enumerate(chunks):
        output_data["chunks"].append({
            "chunk_id": i + 1,
            "description": descriptions[i],
            "start_time": round(chunk["start_time"], 2),
            "end_time": round(chunk["end_time"], 2),
            "duration": round(chunk["duration"], 2),
            "sentences_count": chunk["sentences_count"],
            "full_text": chunk["full_text"],
            "sentences": [
                {
                    "text": s["text"],
                    "start": round(s.get("start", 0), 2),
                    "end": round(s.get("end", 0), 2)
                }
                for s in chunk["sentences"]
            ]
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Saved JSON output to {output_path.name}")


def save_markdown_output(chunks: List[Dict], descriptions: List[str], output_path: Path) -> None:
    """Save chunks to Markdown format."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {output_path.stem.replace('_chunked', '').replace('_', ' ').title()} - Semantic Chunks\n\n")

        for i, chunk in enumerate(chunks):
            chunk_id = i + 1
            description = descriptions[i]
            start_time = format_time(chunk["start_time"])
            end_time = format_time(chunk["end_time"])

            f.write(f"## Chunk {chunk_id}: {description}\n\n")
            f.write(f"**Time**: {start_time} - {end_time} | **Sentences**: {chunk['sentences_count']}\n\n")
            f.write(chunk["full_text"])
            f.write("\n\n---\n\n")

    print(f"  ✓ Saved Markdown output to {output_path.name}")


def process_single_lesson(lesson_path: Path, output_base_dir: Path):
    """Processes a single lesson folder."""
    print(f"\n{'=' * 60}")
    print(f"PROCESSING LESSON: {lesson_path.parent.name}/{lesson_path.name}")
    print(f"{'=' * 60}")

    # Phase 1: Load data
    print("\n[Phase 1] Loading and extracting sentences...")
    sentences = load_json_files(lesson_path)
    if not sentences:
        print(f"⚠ No sentences found in {lesson_path}. Skipping.")
        return

    # Phase 2: Generate embeddings
    print("\n[Phase 2] Generating embeddings...")
    embeddings, texts = generate_embeddings(sentences)

    # Phase 3: Cluster sentences
    print("\n[Phase 3] Clustering sentences...")
    clusters = cluster_sentences(embeddings, sentences)
    if N_CLUSTERS is None:  # Only merge small clusters if not using a fixed N_CLUSTERS
        clusters = merge_small_clusters(clusters)

    # Phase 4: Create chunk objects
    print("\n[Phase 4] Creating chunk objects...")
    chunks = create_chunks(sentences, clusters, texts)

    # Phase 5: Generate descriptions
    print("\n[Phase 5] Generating descriptions...")
    descriptions = generate_chunk_descriptions(chunks, texts)

    # Phase 6: Save outputs
    print("\n[Phase 6] Saving outputs...")
    # Dynamic output filenames based on lesson_path
    lesson_name = lesson_path.name
    student_name = lesson_path.parent.name
    json_output = output_base_dir / f"{student_name}_{lesson_name}_chunked.json"
    markdown_output = output_base_dir / f"{student_name}_{lesson_name}_chunked.md"

    save_json_output(chunks, descriptions, json_output)
    save_markdown_output(chunks, descriptions, markdown_output)

    print("\n" + "=" * 60)
    print(f"✓ Processing complete for {lesson_path.parent.name}/{lesson_path.name}!")
    print(f"  - Chunks created: {len(chunks)}")
    print(f"  - Total duration: {format_time(sum(c['duration'] for c in chunks))}")
    print(f"  - JSON output: {json_output.relative_to(REPO_ROOT)}")
    print(f"  - Markdown output: {markdown_output.relative_to(REPO_ROOT)}")
    print("=" * 60)


def main():
    """Main execution loop to find and process all student lessons."""
    print("=" * 60)
    print("BATCH SEMANTIC CHUNKING FOR LESSON TRANSCRIPTS")
    print("=" * 60)
    print(f"Repository root: {REPO_ROOT}")
    print(f"Data path: {DATA_PATH}")
    print(f"Output directory: {OUTPUT_DIR}")

    # Create the output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Find all student directories (e.g., Student-1, Student-2) under DATA_PATH
    student_dirs = sorted(DATA_PATH.glob("Student-*"))

    if not student_dirs:
        print(f"\n❌ No student directories found under {DATA_PATH}. Please check the path.")
        return

    print(f"\nFound {len(student_dirs)} student directory/directories\n")

    total_processed_lessons = 0
    for student_dir in student_dirs:
        print(f"\n\n{'#' * 70}")
        print(f"PROCESSING STUDENT FOLDER: {student_dir.name}")
        print(f"{'#' * 70}")

        # Find all lesson directories (e.g., lesson-1, lesson-2) within each student directory
        lesson_dirs = sorted(student_dir.glob("lesson-*"))

        if not lesson_dirs:
            print(f"⚠ No lesson directories found in {student_dir.name}. Skipping this student.")
            continue

        for lesson_dir in lesson_dirs:
            process_single_lesson(lesson_dir, OUTPUT_DIR)
            total_processed_lessons += 1

    print(f"\n\n{'=' * 70}")
    print(f"✓ BATCH PROCESSING COMPLETE! Total lessons processed: {total_processed_lessons}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
