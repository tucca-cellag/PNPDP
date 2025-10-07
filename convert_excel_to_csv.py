#!/usr/bin/env python3
"""
Excel to CSV Converter for HPC Species Proteome and BLAST Analysis Pipeline

This script converts an Excel file containing species data to the CSV format
required by the workflow.

Usage:
    python convert_excel_to_csv.py <input_file.xlsx> [output_file.csv]

Example:
    python convert_excel_to_csv.py your_file.xlsx species.csv
"""

import pandas as pd
import sys
import os


def convert_excel_to_csv(input_file, output_file="species.csv"):
    """
    Convert Excel file to CSV format for the workflow.

    Args:
        input_file (str): Path to input Excel file
        output_file (str): Path to output CSV file (default: 'species.csv')
    """

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return False

    try:
        # Read the Excel file
        print(f"Reading Excel file: {input_file}")
        df = pd.read_excel(input_file)

        print(f"Original data: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"Available columns: {list(df.columns)}")

        # Check if required columns exist
        required_columns = [
            "Culture ID",
            "Accepted Name (link)",
            "Legacy Name",
            "Genus",
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"Warning: Missing columns: {missing_columns}")
            print(
                "Please adjust the column names in this script to match your Excel file."
            )
            return False

        # Create a simplified dataframe with the columns we need
        species_df = pd.DataFrame(
            {
                "cell_line": df["Culture ID"],  # Use Culture ID as cell line identifier
                "Accepted name": df["Accepted Name (link)"],
                "Legacy Name": df["Legacy Name"],
                "Genus": df["Genus"],
            }
        )

        # Remove duplicates based on all taxonomic fields
        initial_count = len(species_df)
        species_df = species_df.drop_duplicates(
            subset=["Accepted name", "Legacy Name", "Genus"]
        )
        removed_duplicates = initial_count - len(species_df)

        if removed_duplicates > 0:
            print(
                f"Removed {removed_duplicates} duplicate species (based on Accepted name, Legacy Name, and Genus)"
            )

        print(f"Final data: {len(species_df)} unique species")

        # Clean up formatting (remove tabs and extra whitespace)
        species_df["Genus"] = species_df["Genus"].str.strip().str.replace("\t", "")
        species_df["Accepted name"] = species_df["Accepted name"].str.strip()
        species_df["Legacy Name"] = species_df["Legacy Name"].str.strip()

        # Save to CSV
        species_df.to_csv(output_file, index=False)
        print(f"Successfully saved to: {output_file}")

        # Show sample of the data
        print("\nFirst 5 rows of converted data:")
        print(species_df.head())

        return True

    except Exception as e:
        print(f"Error converting file: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python convert_excel_to_csv.py <input_file.xlsx> [output_file.csv]"
        )
        print("Example: python convert_excel_to_csv.py your_file.xlsx species.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "species.csv"

    success = convert_excel_to_csv(input_file, output_file)

    if success:
        print(f"\n✅ Conversion completed successfully!")
        print(f"📁 Output file: {output_file}")
        print(
            f"🔧 Next step: Update config/config.yaml to use '{output_file}' as your species_csv"
        )
    else:
        print(f"\n❌ Conversion failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
