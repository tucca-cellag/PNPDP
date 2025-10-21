#!/usr/bin/env python3
"""
Generate species names file from species.csv for plantiSMASH coverage analysis.

This script extracts unique species names from the main species CSV file and
creates a simple text file with one species name per line. The output file
is formatted for use with plantiSMASH coverage analysis tools, starting with
an empty line followed by sorted species names.
"""
import pandas as pd
import sys
import argparse


def generate_species_names(input_csv, output_file):
    """Generate species names file from CSV."""
    print("Reading species from CSV...")
    df = pd.read_csv(input_csv)
    species_names = df["Accepted name"].dropna().unique()

    print(f"Found {len(species_names)} unique species")

    print("Writing species names to file...")
    with open(output_file, "w") as f:
        f.write("\n")  # Empty first line to match original format
        for species in sorted(species_names):
            f.write(f"{species}\n")

    print(f"Generated {output_file} with {len(species_names)} species")


def main():
    parser = argparse.ArgumentParser(description="Generate species names file")
    parser.add_argument("input_csv", help="Input CSV file path")
    parser.add_argument("output_file", help="Output species names file path")

    args = parser.parse_args()
    generate_species_names(args.input_csv, args.output_file)


if __name__ == "__main__":
    main()
