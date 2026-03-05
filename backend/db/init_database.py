"""Script pour initialiser la base de données JARVIS 2.0"""

import asyncio
import aiosqlite
from pathlib import Path


async def init_database():
    """Initialise la base de données avec le schéma complet"""
    db_path = Path(__file__).parent / "jarvis.db"
    schema_file = Path(__file__).parent / "schema.sql"

    print("=" * 60)
    print("Initialisation Base de Données JARVIS 2.0")
    print("=" * 60)
    print(f"📂 Base de données: {db_path}")
    print(f"📄 Schéma: {schema_file}")

    if not schema_file.exists():
        print(f"❌ Fichier schema.sql introuvable: {schema_file}")
        return False

    # Lire le schéma SQL
    schema_sql = schema_file.read_text(encoding="utf-8")

    print(f"\n🔧 Exécution du schéma SQL...\n")

    try:
        async with aiosqlite.connect(db_path) as db:
            # Exécuter le schéma complet en une fois
            await db.executescript(schema_sql)
            await db.commit()
            print("  ✅ Schéma exécuté avec succès")

        print("\n✅ Base de données initialisée avec succès!")
        
        # Vérifier les tables créées
        await verify_tables(db_path)
        
        return True

    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {e}")
        return False


async def verify_tables(db_path):
    """Vérifie que toutes les tables ont été créées"""
    print("\n🔍 Vérification des tables...\n")

    expected_tables = [
        "projects",
        "conversations",
        "messages",
        "library_documents"
    ]

    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ) as cursor:
            tables = await cursor.fetchall()
            table_names = [t[0] for t in tables]

            for table in expected_tables:
                if table in table_names:
                    # Compter les lignes
                    async with db.execute(f"SELECT COUNT(*) FROM {table}") as count_cursor:
                        count = await count_cursor.fetchone()
                        print(f"  ✅ Table '{table}' créée ({count[0]} lignes)")
                else:
                    print(f"  ❌ Table '{table}' manquante")

    print("\n✅ Vérification terminée!")


async def main():
    success = await init_database()
    
    if success:
        print("\n" + "=" * 60)
        print("Prochaine étape : Appliquer la migration 004")
        print("=" * 60)
        print("Commande : python backend/db/migrations/apply_migration.py")
    else:
        print("\n⚠️  L'initialisation a échoué. Vérifiez les erreurs ci-dessus.")


if __name__ == "__main__":
    asyncio.run(main())
