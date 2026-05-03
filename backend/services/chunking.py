"""
chunking.py — Découpage automatique des missions code selon limites modèle.
Stratégies implémentées (V1) : single_call, chunk_by_file.
chunk_by_block reporté en V2 (YAGNI assumé).
"""
import logging

logger = logging.getLogger("jarvis")

# Heuristique tokens : 1 token ≈ 3.5 chars (moyenne pondérée code/texte)
TOKENS_PER_CHAR = 1 / 3.5

# Fenêtres modèles (en tokens) — table figée pour V1
MODEL_WINDOWS = {
    "anthropic/claude-haiku-4.5": 200_000,
    "anthropic/claude-sonnet-4.5": 1_000_000,
    "google/gemini-2.5-flash": 1_000_000,
    "google/gemini-2.5-pro": 1_048_576,
}

# Marge réservée pour la sortie LLM (en tokens)
OUTPUT_MARGIN = 8_000

# Overhead système (en tokens)
SYSTEM_OVERHEAD = 2_000

# Fenêtre par défaut si modèle inconnu
_DEFAULT_WINDOW = 200_000


def estimate_tokens(text: str) -> int:
    """Heuristique simple : 1 token ≈ 3.5 chars."""
    if not text:
        return 0
    return max(1, int(len(text) * TOKENS_PER_CHAR))


def estimate_tokens_budget(
    mission_prompt: str,
    targeted_files_content: dict,
    model_id: str,
) -> dict:
    """
    Évalue si la mission tient dans la fenêtre du modèle.

    Retourne :
    {
      "model_window": int,
      "prompt_tokens_estimated": int,
      "files_tokens_estimated": int,
      "system_overhead": int,
      "output_margin": int,
      "total_input_estimated": int,
      "fits_in_one_call": bool,
      "recommended_strategy": "single_call" | "chunk_by_file"
    }
    Si total > model_window - output_margin → chunk_by_file
    Sinon → single_call
    """
    model_window = MODEL_WINDOWS.get(model_id, _DEFAULT_WINDOW)
    prompt_tokens = estimate_tokens(mission_prompt)
    files_tokens = sum(estimate_tokens(content) for content in targeted_files_content.values())
    total_input = prompt_tokens + files_tokens + SYSTEM_OVERHEAD
    fits = total_input <= model_window - OUTPUT_MARGIN
    return {
        "model_window": model_window,
        "prompt_tokens_estimated": prompt_tokens,
        "files_tokens_estimated": files_tokens,
        "system_overhead": SYSTEM_OVERHEAD,
        "output_margin": OUTPUT_MARGIN,
        "total_input_estimated": total_input,
        "fits_in_one_call": fits,
        "recommended_strategy": "single_call" if fits else "chunk_by_file",
    }


def split_mission_by_files(
    mission_data: dict,
    files_content: dict,
    model_id: str,
) -> list:
    """
    Découpe la mission en sous-tâches (1 par fichier ciblé).

    Chaque sous-tâche reçoit :
    - L'objectif global de la mission
    - Le contexte projet (réutilisé)
    - UN SEUL fichier à modifier
    - L'output cumulé des fichiers déjà traités (si dépendance)

    Retourne liste de dicts :
    [
      {
        "sub_step_index": 0,
        "file_path": "frontend/foo.html",
        "prompt": "<prompt construit>",
        "tokens_estimated": int
      },
      ...
    ]
    Si un seul fichier dépasse le budget : raise
    ValueError("Mission trop volumineuse — découpe côté Réflexion")
    """
    model_window = MODEL_WINDOWS.get(model_id, _DEFAULT_WINDOW)
    available_tokens = model_window - OUTPUT_MARGIN - SYSTEM_OVERHEAD

    objectif = mission_data.get("objectif", "")
    contexte = mission_data.get("contexte", "")
    contraintes = mission_data.get("contraintes", [])
    criteres = mission_data.get("criteres_reussite", [])

    base_parts = [f"OBJECTIF GLOBAL:\n{objectif}"]
    if contexte:
        base_parts.append(f"CONTEXTE PROJET:\n{contexte}")
    if contraintes:
        base_parts.append("CONTRAINTES:\n" + "\n".join(f"- {c}" for c in contraintes))
    if criteres:
        base_parts.append("CRITÈRES DE RÉUSSITE:\n" + "\n".join(f"- {c}" for c in criteres))
    base_prompt = "\n\n".join(base_parts)
    base_tokens = estimate_tokens(base_prompt)

    total_files = len(files_content)
    sub_tasks = []
    cumulated_output = ""

    for idx, (file_path, file_content) in enumerate(files_content.items()):
        file_tokens = estimate_tokens(file_content)

        if file_tokens + base_tokens > available_tokens:
            raise ValueError(
                f"Mission trop volumineuse — découpe côté Réflexion "
                f"(fichier '{file_path}' ≈ {file_tokens} tokens dépasse le budget disponible "
                f"de {available_tokens} tokens)"
            )

        sub_parts = [f"OBJECTIF GLOBAL DE LA MISSION:\n{objectif}"]
        if contexte:
            sub_parts.append(f"CONTEXTE PROJET:\n{contexte}")
        sub_parts.append(
            f"FICHIER À MODIFIER ({idx + 1}/{total_files}):\n"
            f"Chemin : {file_path}\n"
            f"Contenu actuel :\n```\n{file_content}\n```"
        )
        if cumulated_output:
            sub_parts.append(
                f"FICHIERS DÉJÀ TRAITÉS (pour cohérence avec les dépendances) :\n{cumulated_output}"
            )
        if contraintes:
            sub_parts.append("CONTRAINTES:\n" + "\n".join(f"- {c}" for c in contraintes))
        if criteres:
            sub_parts.append("CRITÈRES DE RÉUSSITE:\n" + "\n".join(f"- {c}" for c in criteres))
        sub_parts.append(
            f"INSTRUCTION : Génère uniquement le code modifié pour le fichier {file_path}. "
            f"Utilise le format :\n```lang\n# {file_path}\ncontenu complet du fichier modifié\n```"
        )

        sub_prompt = "\n\n".join(sub_parts)

        sub_tasks.append({
            "sub_step_index": idx,
            "file_path": file_path,
            "prompt": sub_prompt,
            "tokens_estimated": estimate_tokens(sub_prompt),
        })

    return sub_tasks


def merge_code_outputs(outputs: list) -> str:
    """
    Concatène les outputs des sous-appels en respectant le format attendu
    par apply_code_blocks_to_project.
    Conserve l'ordre des sub_step_index.
    """
    merged_parts = []
    for output in outputs:
        if output and output.strip():
            merged_parts.append(output.strip())
    return "\n\n".join(merged_parts)
