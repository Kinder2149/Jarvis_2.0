"""Script pour appliquer la migration 004 - Versioning et métriques"""

import asyncio
import aiosqlite
from pathlib import Path


async def apply_migration_004():
    """Applique la migration 004 pour ajouter versioning et métriques"""
    db_path = Path(__file__).parent.parent / "jarvis.db"
    migration_file = Path(__file__).parent / "004_library_versioning_metrics.sql"

    print(f"📂 Base de données: {db_path}")
    print(f"📄 Migration: {migration_file}")

    if not migration_file.exists():
        print(f"❌ Fichier de migration introuvable: {migration_file}")
        return False

    # Lire le fichier SQL
    migration_sql = migration_file.read_text(encoding="utf-8")

    print(f"\n🔧 Application de la migration...\n")

    try:
        async with aiosqlite.connect(db_path) as db:
            # Exécuter le script SQL complet en une fois
            try:
                await db.executescript(migration_sql)
                await db.commit()
                print("  ✅ Migration appliquée avec succès")
            except aiosqlite.OperationalError as e:
                error_msg = str(e)
                # Ignorer les erreurs de colonnes/tables déjà existantes
                if "duplicate column" in error_msg or "already exists" in error_msg:
                    print(f"  ⚠️  Certains éléments existent déjà (migration déjà appliquée partiellement)")
                    print(f"  ℹ️  Détail: {error_msg}")
                    await db.commit()
                else:
                    raise

        print("\n✅ Migration 004 appliquée avec succès!")
        return True

    except Exception as e:
        print(f"\n❌ Erreur lors de l'application de la migration: {e}")
        return False


async def verify_migration():
    """Vérifie que la migration a été appliquée correctement"""
    db_path = Path(__file__).parent.parent / "jarvis.db"

    print("\n🔍 Vérification de la migration...\n")

    async with aiosqlite.connect(db_path) as db:
        # Vérifier les nouvelles colonnes de library_documents
        async with db.execute("PRAGMA table_info(library_documents)") as cursor:
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]

            expected_columns = ["version", "previous_version_id", "is_active"]
            for col in expected_columns:
                if col in column_names:
                    print(f"  ✅ Colonne '{col}' présente dans library_documents")
                else:
                    print(f"  ❌ Colonne '{col}' manquante dans library_documents")

        # Vérifier les nouvelles tables
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ) as cursor:
            tables = await cursor.fetchall()
            table_names = [t[0] for t in tables]

            expected_tables = [
                "library_document_versions",
                "library_document_metrics",
                "library_access_logs",
            ]
            for table in expected_tables:
                if table in table_names:
                    print(f"  ✅ Table '{table}' créée")
                else:
                    print(f"  ❌ Table '{table}' manquante")

    print("\n✅ Vérification terminée!")


async def main():
    print("=" * 60)
    print("Migration 004 - Versioning et Métriques Library")
    print("=" * 60)

    success = await apply_migration_004()

    if success:
        await verify_migration()
    else:
        print("\n⚠️  La migration a échoué. Vérifiez les erreurs ci-dessus.")


if __name__ == "__main__":
    asyncio.run(main())
