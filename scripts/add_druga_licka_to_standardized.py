"""
Add Druga Lička Proleterska Brigada soldiers to the standardized Excel file.
"""

import sys
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main():
    # Read the extracted data
    druga_licka_csv = Path("01-data/processed/druga_licka_proleterska_soldiers.csv")
    standardized_xlsx = Path("01-data/processed/standardized_soldiers.xlsx")

    print(f"Reading {druga_licka_csv}...")
    df_druga = pd.read_csv(druga_licka_csv, encoding='utf-8-sig')

    print(f"Reading {standardized_xlsx}...")
    df_standard = pd.read_excel(standardized_xlsx)

    print(f"Current standardized file columns: {df_standard.columns.tolist()}")
    print(f"Current brigades in standardized file: {df_standard['Source/Brigade'].unique()}")
    print(f"Current total soldiers: {len(df_standard)}")

    # Map Druga Lička columns to standardized format
    # Standardized columns: ['Last Name', 'Middle Name', 'First Name', 'Full Name',
    #                        'Date of Birth', 'Birth Year', 'Additional Information', 'Source/Brigade']

    df_new = pd.DataFrame()
    df_new['Last Name'] = df_druga['last_name']
    df_new['Middle Name'] = df_druga['middle_name']
    df_new['First Name'] = df_druga['first_name']

    # Create full name
    def create_full_name(row):
        parts = []
        if pd.notna(row['First Name']) and row['First Name']:
            parts.append(str(row['First Name']))
        if pd.notna(row['Middle Name']) and row['Middle Name']:
            parts.append(str(row['Middle Name']))
        if pd.notna(row['Last Name']) and row['Last Name']:
            parts.append(str(row['Last Name']))
        return ' '.join(parts) if parts else ''

    df_new['Full Name'] = df_new.apply(create_full_name, axis=1)
    df_new['Date of Birth'] = ''  # Not available in this format
    df_new['Birth Year'] = df_druga['birth_year']
    df_new['Additional Information'] = df_druga['additional_info']
    df_new['Source/Brigade'] = 'Druga Lička Proleterska Brigada'

    # Combine with existing data
    df_combined = pd.concat([df_standard, df_new], ignore_index=True)

    print(f"\nAdded {len(df_new)} soldiers from Druga Lička brigade")
    print(f"New total soldiers: {len(df_combined)}")
    print(f"Brigades now: {df_combined['Source/Brigade'].unique()}")

    # Save back to Excel
    df_combined.to_excel(standardized_xlsx, index=False)
    print(f"\nSaved to {standardized_xlsx}")

    # Also save Druga Lička as separate Excel
    druga_licka_xlsx = Path("01-data/processed/druga_licka_proleterska_soldiers.xlsx")
    df_new.to_excel(druga_licka_xlsx, index=False)
    print(f"Saved separate file: {druga_licka_xlsx}")


if __name__ == "__main__":
    main()
