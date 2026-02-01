"""
Database utility functions for working with soldier records.
Can be used as a module or run as CLI for quick queries.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import sqlite3
from pathlib import Path
from datetime import datetime

DATABASE_PATH = Path("01-data/soldiers.db")


def get_connection():
    """Get database connection with row factory."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# READ OPERATIONS
# ============================================================================

def get_soldier(soldier_id: str) -> dict:
    """Get a single soldier by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, b.name as brigade_name
        FROM soldiers s
        JOIN brigades b ON s.brigade_code = b.code
        WHERE s.soldier_id = ?
    """, (soldier_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def search_soldiers(query: str, limit: int = 50) -> list:
    """Full-text search for soldiers."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.soldier_id, s.last_name, s.first_name, s.middle_name,
               s.additional_info, b.name as brigade_name
        FROM soldiers_fts
        JOIN soldiers s ON soldiers_fts.soldier_id = s.soldier_id
        JOIN brigades b ON s.brigade_code = b.code
        WHERE soldiers_fts MATCH ?
        LIMIT ?
    """, (query, limit))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def search_by_name(last_name: str = None, first_name: str = None, limit: int = 50) -> list:
    """Search by exact or partial name."""
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if last_name:
        conditions.append("s.last_name LIKE ?")
        params.append(f"%{last_name}%")
    if first_name:
        conditions.append("s.first_name LIKE ?")
        params.append(f"%{first_name}%")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    cursor.execute(f"""
        SELECT s.soldier_id, s.last_name, s.first_name, s.middle_name,
               s.additional_info, b.name as brigade_name
        FROM soldiers s
        JOIN brigades b ON s.brigade_code = b.code
        WHERE {where_clause}
        ORDER BY s.last_name, s.first_name
        LIMIT ?
    """, params + [limit])

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_stats() -> dict:
    """Get database statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    stats = {'brigades': [], 'totals': {}}

    # Per brigade
    cursor.execute("""
        SELECT b.code, b.name,
               COUNT(s.soldier_id) as total,
               SUM(s.ai_processed) as ai_done,
               SUM(s.manually_reviewed) as reviewed
        FROM brigades b
        LEFT JOIN soldiers s ON b.code = s.brigade_code
        GROUP BY b.code
        ORDER BY b.code
    """)
    for row in cursor.fetchall():
        stats['brigades'].append({
            'code': row['code'],
            'name': row['name'],
            'total': row['total'],
            'ai_done': row['ai_done'] or 0,
            'reviewed': row['reviewed'] or 0
        })

    # Totals
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(ai_processed) as ai_done,
               SUM(manually_reviewed) as reviewed
        FROM soldiers
    """)
    row = cursor.fetchone()
    stats['totals'] = {
        'total': row['total'],
        'ai_done': row['ai_done'] or 0,
        'reviewed': row['reviewed'] or 0
    }

    conn.close()
    return stats


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================

def update_soldier(soldier_id: str, **fields) -> bool:
    """Update soldier fields. Returns True if updated."""
    if not fields:
        return False

    # Add updated_at
    fields['updated_at'] = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
    values = list(fields.values()) + [soldier_id]

    cursor.execute(f"""
        UPDATE soldiers
        SET {set_clause}
        WHERE soldier_id = ?
    """, values)

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def mark_reviewed(soldier_id: str, notes: str = None) -> bool:
    """Mark a soldier as manually reviewed."""
    return update_soldier(soldier_id, manually_reviewed=1, review_notes=notes)


def update_ai_extraction(soldier_id: str, ai_result: dict) -> bool:
    """Update soldier with AI extraction results."""
    return update_soldier(
        soldier_id,
        ai_processed=1,
        ai_confidence=ai_result.get('confidence', ''),
        ai_parsing_issues=', '.join(ai_result.get('parsing_issues', [])),
        ai_fathers_name=ai_result.get('fathers_name', ''),
        ai_birth_year=ai_result.get('birth_year', ''),
        ai_birthplace=ai_result.get('birthplace', ''),
        ai_military_unit=ai_result.get('military_unit', ''),
        ai_rank_or_role=ai_result.get('rank_or_role', ''),
        ai_death_date=ai_result.get('death_date', ''),
        ai_death_place=ai_result.get('death_place', ''),
        ai_death_cause=ai_result.get('death_cause', ''),
        ai_other_info=ai_result.get('other_info', '')
    )


# ============================================================================
# CLI
# ============================================================================

def print_soldier(s: dict):
    """Pretty print a soldier record."""
    print(f"\n  ID: {s['soldier_id']}")
    print(f"  Name: {s['last_name']} {s.get('middle_name', '')} {s['first_name']}")
    print(f"  Brigade: {s.get('brigade_name', s.get('brigade_code', '?'))}")
    if s.get('additional_info'):
        print(f"  Info: {s['additional_info'][:80]}...")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Soldier database utilities')
    subparsers = parser.add_subparsers(dest='command')

    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')

    # Search command
    search_p = subparsers.add_parser('search', help='Search soldiers')
    search_p.add_argument('query', help='Search query')
    search_p.add_argument('-n', '--limit', type=int, default=10, help='Max results')

    # Get command
    get_p = subparsers.add_parser('get', help='Get soldier by ID')
    get_p.add_argument('soldier_id', help='10-digit soldier ID')

    # Name search
    name_p = subparsers.add_parser('name', help='Search by name')
    name_p.add_argument('-l', '--last', help='Last name')
    name_p.add_argument('-f', '--first', help='First name')
    name_p.add_argument('-n', '--limit', type=int, default=10, help='Max results')

    args = parser.parse_args()

    if args.command == 'stats':
        stats = get_stats()
        print("\n" + "=" * 60)
        print("DATABASE STATISTICS")
        print("=" * 60)
        print(f"\n{'Brigade':<35} {'Total':>8} {'AI':>8} {'Reviewed':>8}")
        print("-" * 60)
        for b in stats['brigades']:
            print(f"{b['name']:<35} {b['total']:>8} {b['ai_done']:>8} {b['reviewed']:>8}")
        print("-" * 60)
        t = stats['totals']
        print(f"{'TOTAL':<35} {t['total']:>8} {t['ai_done']:>8} {t['reviewed']:>8}")

    elif args.command == 'search':
        results = search_soldiers(args.query, args.limit)
        print(f"\nSearch '{args.query}': {len(results)} results")
        for s in results:
            print_soldier(s)

    elif args.command == 'get':
        soldier = get_soldier(args.soldier_id)
        if soldier:
            print("\nSoldier Record:")
            for k, v in soldier.items():
                if v:
                    print(f"  {k}: {v}")
        else:
            print(f"Soldier not found: {args.soldier_id}")

    elif args.command == 'name':
        results = search_by_name(args.last, args.first, args.limit)
        print(f"\nName search: {len(results)} results")
        for s in results:
            print_soldier(s)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
