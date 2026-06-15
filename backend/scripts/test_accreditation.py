"""
Examen blanc — Accréditation WFDF Standard
20 questions QCM soumises à l'agent DISC via l'API JARVIS.
Usage : python backend/scripts/test_accreditation.py
"""
import httpx
import asyncio
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"

# (id, question, [options A/B/C/D], bonne_réponse, ref_article)
QUESTIONS = [
    (1,
     "La ligne de périmètre du terrain (sideline) fait-elle partie du terrain de jeu ?",
     ["A) Oui, elle est in-bounds",
      "B) Non, elle est hors-limites (out-of-bounds)",
      "C) Elle est neutre : ni in, ni out",
      "D) Cela dépend si le disque la touche ou si un joueur la touche"],
     "B", "§2 Terrain"),

    (2,
     "Qui est autorisé à effectuer le stall count ?",
     ["A) N'importe quel défenseur",
      "B) Le capitaine de l'équipe défensive",
      "C) Le seul défenseur qui marque directement le porteur du disque",
      "D) N'importe quel joueur sur le terrain"],
     "C", "§9"),

    (3,
     "Un joueur saute depuis in-bounds, attrape le disque dans les airs puis atterrit hors-limites."
     " La réception est-elle valide ?",
     ["A) Non : il a atterri OOB donc la réception est invalide",
      "B) Oui : il était in-bounds au moment du contrôle du disque",
      "C) Non : il faut rejouer le point",
      "D) Le disque revient au lanceur précédent"],
     "B", "§10.1"),

    (4,
     "Que se passe-t-il quand le stall count atteint 10 ?",
     ["A) Le lanceur dispose de 3 secondes supplémentaires",
      "B) C'est un turnover : la possession passe à l'équipe adverse",
      "C) Un time-out automatique est accordé",
      "D) Le compte repart à stall 1"],
     "B", "§9"),

    (5,
     "Après un appel (call) accepté par les deux parties, comment reprend-on le jeu ?",
     ["A) Le jeu reprend immédiatement sans procédure particulière",
      "B) Le porteur relance depuis l'endroit où il se trouvait au moment de l'appel, stall 1",
      "C) Le point est rejoué depuis le pull",
      "D) L'équipe adverse prend la possession"],
     "B", "§8 / §13"),

    (6,
     "Un défenseur arrache le disque des mains du porteur qui en avait clairement le contrôle."
     " Comment appelle-t-on cette faute ?",
     ["A) Travel",
      "B) Pick",
      "C) Strip",
      "D) Fast count"],
     "C", "§14.1"),

    (7,
     "Combien de défenseurs peuvent se trouver simultanément à moins de 3 mètres du porteur"
     " sans que ce soit une violation de double team ?",
     ["A) Autant que nécessaire",
      "B) Deux maximum",
      "C) Un seul (le marqueur direct)",
      "D) Trois maximum"],
     "C", "§15.2"),

    (8,
     "À quel moment un point est-il marqué ?",
     ["A) Quand le disque touche le sol dans la end zone adverse",
      "B) Quand un attaquant complète une réception dans la end zone adverse, in-bounds",
      "C) Quand le disque franchit la ligne de but en l'air",
      "D) Quand le lanceur envoie le disque depuis sa propre end zone"],
     "B", "§12"),

    (9,
     "Un joueur déplace son pied de pivot avant de lâcher le disque."
     " Comment appelle-t-on cette infraction ?",
     ["A) Strip",
      "B) Double team",
      "C) Fast count",
      "D) Travel"],
     "D", "§15.1"),

    (10,
     "Que signifie le Spirit of the Game (SOTG) en Ultimate ?",
     ["A) Une célébration obligatoire après chaque point",
      "B) La responsabilité de chaque joueur de jouer fair-play et d'auto-arbitrer honnêtement",
      "C) Une règle sur les encouragements entre coéquipiers",
      "D) L'obligation de serrer la main après le match uniquement"],
     "B", "§1"),

    (11,
     "Un défenseur commet une faute sur le récepteur dans la end zone, la faute est acceptée."
     " Que se passe-t-il ?",
     ["A) Le disque revient au lanceur",
      "B) Le point est accordé",
      "C) Un penalty est accordé à l'attaque",
      "D) La possession est donnée au porteur depuis la ligne de but"],
     "B", "§14.3"),

    (12,
     "Après un turnover out-of-bounds, depuis où l'équipe qui récupère la possession doit-elle reprendre ?",
     ["A) Depuis n'importe où sur le terrain",
      "B) Depuis sa propre end zone",
      "C) Depuis le point brick le plus proche ou l'endroit exact de sortie (le plus avantageux)",
      "D) Depuis le milieu du terrain"],
     "C", "§8.1"),

    (13,
     "Le stall count est à 'stall 6'. Le porteur appelle Fast count (accepté)."
     " À quel nombre le compte repart-il ?",
     ["A) Stall 1",
      "B) Stall 4",
      "C) Stall 6",
      "D) Stall 7"],
     "B", "§9.2"),

    (14,
     "Qu'est-ce qu'un Pick en Ultimate ?",
     ["A) Quand le porteur marche avec le disque sans établir son pivot",
      "B) Quand un attaquant bloque involontairement le chemin d'un défenseur qui suit un autre attaquant",
      "C) Quand deux défenseurs se trouvent près du porteur simultanément",
      "D) Quand le disque est arraché au porteur"],
     "B", "§15.4"),

    (15,
     "Un appel est contesté : les deux joueurs ne se mettent pas d'accord. Que se passe-t-il ?",
     ["A) Un observateur tranche",
      "B) Le capitaine de l'équipe défensive décide",
      "C) Le disque revient au dernier lanceur incontesté, stall 1",
      "D) Le point est rejoué depuis le pull"],
     "C", "§2.D / §13"),

    (16,
     "La ligne de fond (end zone line) fait-elle partie de la end zone ?",
     ["A) Non, elle est hors-limites",
      "B) Oui, elle fait partie de la end zone",
      "C) Non, elle est neutre",
      "D) Cela dépend du niveau de jeu"],
     "B", "§10.3"),

    (17,
     "Quelle est la longueur de la zone centrale de jeu (sans les end zones) sur un terrain officiel WFDF ?",
     ["A) 70 mètres",
      "B) 64 mètres",
      "C) 100 mètres",
      "D) 82 mètres"],
     "B", "§2"),

    (18,
     "Après un appel accepté par le marqueur, à combien repart le stall count ?",
     ["A) Au nombre où il était au moment de l'appel",
      "B) À stall 1",
      "C) À stall [N+1] (nombre au moment de l'appel + 1)",
      "D) Il ne repart jamais à 1, seulement en cas de blessure"],
     "B", "§9.1"),

    (19,
     "Qui peut demander un Spirit Time-out ?",
     ["A) Uniquement les capitaines des deux équipes",
      "B) Uniquement le porteur du disque",
      "C) N'importe quel joueur sur le terrain",
      "D) Uniquement les coaches ou officiels"],
     "C", "§16.1"),

    (20,
     "Le pull sort hors-limites sans être touché par l'attaque. Quelle est l'option de l'équipe attaquante ?",
     ["A) Rejouer le pull depuis le début",
      "B) Reprendre depuis sa propre end zone OU depuis le point brick (au choix de l'attaque)",
      "C) Reprendre depuis le milieu du terrain",
      "D) L'équipe défensive rejoue le pull depuis sa end zone"],
     "B", "§7"),
]


async def ask_disc(question_text: str) -> str:
    async with httpx.AsyncClient(base_url=BASE, timeout=45) as c:
        r = await c.post("/api/jarvis/conversations", json={"title": "Accreditation test"})
        conv_id = r.json()["id"]
        prompt = (
            "Question d'accréditation WFDF. "
            "Réponds UNIQUEMENT avec : 'REPONSE: [lettre]' (A, B, C ou D), "
            "puis une justification courte basée sur les règles WFDF 2025-2028.\n\n"
            + question_text
        )
        r2 = await c.post(
            f"/api/jarvis/conversations/{conv_id}/chat",
            json={"message": prompt, "force_agent": "DISC"},
        )
        return r2.json().get("content", "")


def extract_answer(response: str) -> str:
    m = re.search(r"REPONSE\s*:\s*\**([A-D])\**", response, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # fallback : première lettre A-D dans les 150 premiers chars
    m2 = re.search(r"\b([A-D])\b", response[:150])
    if m2:
        return m2.group(1).upper()
    return "?"


async def main():
    print("=" * 68)
    print("EXAMEN BLANC — ACCRÉDITATION WFDF STANDARD")
    print("20 questions QCM | Agent : DISC")
    print("=" * 68)

    score = 0
    wrong = []

    for qid, question, options, correct, ref in QUESTIONS:
        full_q = question + "\n" + "\n".join(options)
        response = await ask_disc(full_q)
        disc_answer = extract_answer(response)
        ok = disc_answer == correct
        if ok:
            score += 1
        else:
            wrong.append((qid, question[:55], correct, disc_answer))

        mark = "✓" if ok else f"✗ (attendu {correct})"

        # Extraire une ligne de justification
        lines = [l.strip() for l in response.split("\n") if l.strip()]
        justif = next(
            (l for l in lines if len(l) > 25 and "REPONSE" not in l.upper()
             and not l.startswith("#")), ""
        )[:95]

        print(f"\nQ{qid:02d} [{ref}]")
        print(f"     {question[:65]}")
        print(f"     DISC={disc_answer} | Attendu={correct} | {mark}")
        if justif:
            print(f"     >> {justif}")

    pct = int(score / len(QUESTIONS) * 100)

    print("\n" + "=" * 68)
    print(f"SCORE FINAL : {score}/{len(QUESTIONS)}  ({pct}%)")

    if pct >= 80:
        niveau = "ACCRÉDITATION STANDARD — OBTENUE ✓"
    elif pct >= 60:
        niveau = "Bon niveau — quelques lacunes à revoir"
    else:
        niveau = "Niveau insuffisant — entraînement requis"
    print(f"NIVEAU      : {niveau}")

    if wrong:
        print("\nQuestions ratées :")
        for qid, q, correct, disc in wrong:
            print(f"  Q{qid:02d} | DISC={disc} | Correct={correct} | {q}...")

    print("\nComparaison accréditation WFDF réelle :")
    print("  Standard  : 80% requis (16/20)")
    print(f"  DISC      : {score}/20 ({pct}%) → {'REUSSI' if pct >= 80 else 'ECHOUE'}")


if __name__ == "__main__":
    asyncio.run(main())
