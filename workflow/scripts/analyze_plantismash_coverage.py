#!/usr/bin/env python3
"""
Analyze coverage of species against plantiSMASH pre-calculated BGCs.

This script compares species in the local dataset against species available
in plantiSMASH's pre-calculated biosynthetic gene cluster (BGC) database.
It performs exact species name matching and genus-level matching to identify
which species already have BGCs available versus those requiring de novo
discovery. The analysis helps prioritize computational resources by identifying
species that can leverage existing plantiSMASH results.

Features:
- Web scraping of plantiSMASH precalc directory
- Species name normalization for robust matching
- Exact and genus-level matching strategies
- Detailed coverage statistics and reporting
- CSV output for downstream analysis
"""

import pandas as pd
import requests
import re
from urllib.parse import urljoin
import time


def normalize_species_name(name):
    """Normalize species name for comparison"""
    # Handle NaN values
    if pd.isna(name) or name is None:
        return ""

    # Convert to string and remove common suffixes and clean up
    name = str(name).strip()
    # Remove genome assembly identifiers (GCA, GCF, etc.)
    name = re.sub(r"\s+GCA\s+[A-Z0-9_.]+.*$", "", name)
    name = re.sub(r"\s+GCF\s+[A-Z0-9_.]+.*$", "", name)
    # Remove 'var.', 'subsp.', 'ssp.', 'f.', 'cv.' etc.
    name = re.sub(r"\s+(var\.|subsp\.|ssp\.|f\.|cv\.|cultivar)\s+.*$", "", name)
    # Remove 'x' for hybrids
    name = re.sub(r"\s+x\s+.*$", "", name)
    # Remove extra spaces and convert to lowercase
    name = re.sub(r"\s+", "_", name.lower())
    return name


def get_plantismash_species():
    """Get list of species from plantiSMASH precalc directory"""
    base_url = "https://plantismash.bioinformatics.nl/precalc/v2/"

    try:
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()

        # Extract species names from HTML links
        species_pattern = r"/precalc/v2/([^/]+)/"
        matches = re.findall(species_pattern, response.text)

        species_list = []
        for match in matches:
            # Clean up the species name
            species_name = match.replace("_", " ").replace(".", "")
            species_list.append(species_name)

        return species_list

    except requests.RequestException as e:
        print(f"Error fetching plantiSMASH data: {e}")
        return []


def analyze_coverage():
    """Analyze coverage of species against plantiSMASH"""

    # Read species from CSV
    print("Reading species from CSV...")
    df = pd.read_csv("resources/species.csv")
    our_species = list(df["Accepted name"].dropna().unique())
    print(f"Found {len(our_species)} unique species in our dataset")

    # Get plantiSMASH species
    print("Fetching plantiSMASH pre-calculated species...")
    plantismash_species = get_plantismash_species()
    print(f"Found {len(plantismash_species)} species in plantiSMASH precalc")

    if not plantismash_species:
        print("Could not fetch plantiSMASH data. Exiting.")
        return

    # Normalize species names for comparison
    print("Normalizing species names for comparison...")
    our_normalized = {
        normalize_species_name(species): species for species in our_species
    }
    plantismash_normalized = {
        normalize_species_name(species): species for species in plantismash_species
    }

    # Find matches
    matches = []
    partial_matches = []

    for species_name in our_species:
        our_norm = normalize_species_name(species_name)

        # Exact match
        if our_norm in plantismash_normalized:
            matches.append((species_name, plantismash_normalized[our_norm]))
        else:
            # Check for genus-level matches
            our_genus = our_norm.split("_")[0]
            for psmash_norm, psmash_orig in plantismash_normalized.items():
                psmash_genus = psmash_norm.split("_")[0]
                if (
                    our_genus == psmash_genus and len(our_genus) > 3
                ):  # Avoid short genus names
                    partial_matches.append((species_name, psmash_orig, our_genus))
                    break

    # Generate report
    print("\n" + "=" * 80)
    print("COVERAGE ANALYSIS REPORT")
    print("=" * 80)

    print(f"\nTotal species in our dataset: {len(our_species)}")
    print(f"Total species in plantiSMASH precalc: {len(plantismash_species)}")
    print(f"Exact matches found: {len(matches)}")
    print(f"Genus-level matches found: {len(partial_matches)}")

    coverage_percentage = (len(matches) / len(our_species)) * 100
    print(f"Coverage percentage (exact matches): {coverage_percentage:.2f}%")

    if matches:
        print(f"\nEXACT MATCHES ({len(matches)}):")
        print("-" * 50)
        for our_species_name, plantismash_species_name in sorted(matches):
            print(f"✓ {our_species_name} -> {plantismash_species_name}")

    if partial_matches:
        print(f"\nGENUS-LEVEL MATCHES ({len(partial_matches)}):")
        print("-" * 50)
        for our_species_name, plantismash_species_name, genus in sorted(
            partial_matches
        ):
            print(
                f"~ {our_species_name} -> {plantismash_species_name} (genus: {genus})"
            )

    # Find unmatched species
    matched_species = {match[0] for match in matches} | {
        match[0] for match in partial_matches
    }
    unmatched = [species for species in our_species if species not in matched_species]

    if unmatched:
        print(f"\nUNMATCHED SPECIES ({len(unmatched)}):")
        print("-" * 50)
        for species in sorted(unmatched)[:20]:  # Show first 20
            print(f"✗ {species}")
        if len(unmatched) > 20:
            print(f"... and {len(unmatched) - 20} more")

    # Save detailed results
    match_types = []
    plantismash_matches = []

    for species in our_species:
        if species in [m[0] for m in matches]:
            match_types.append("Exact")
            # Find the matching plantiSMASH species
            for m in matches:
                if m[0] == species:
                    plantismash_matches.append(m[1])
                    break
        elif species in [m[0] for m in partial_matches]:
            match_types.append("Genus")
            # Find the matching plantiSMASH species
            for m in partial_matches:
                if m[0] == species:
                    plantismash_matches.append(m[1])
                    break
        else:
            match_types.append("No Match")
            plantismash_matches.append("")

    results_df = pd.DataFrame(
        {
            "Our_Species": our_species,
            "Match_Type": match_types,
            "PlantiSMASH_Species": plantismash_matches,
        }
    )

    results_df.to_csv("results/plantismash_coverage_analysis.csv", index=False)
    print("\nDetailed results saved to: results/plantismash_coverage_analysis.csv")

    # Save coverage statistics to text file
    with open("results/plantismash_coverage_stats.txt", "w") as f:
        f.write("PLANTISMASH COVERAGE ANALYSIS STATISTICS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total species in our dataset: {len(our_species)}\n")
        f.write(f"Total species in plantiSMASH precalc: {len(plantismash_species)}\n")
        f.write(f"Exact matches found: {len(matches)}\n")
        f.write(f"Genus-level matches found: {len(partial_matches)}\n")
        f.write(f"No matches: {len(unmatched)}\n\n")

        f.write("COVERAGE PERCENTAGES:\n")
        f.write("-" * 25 + "\n")
        exact_coverage = (len(matches) / len(our_species)) * 100
        genus_coverage = (len(partial_matches) / len(our_species)) * 100
        total_coverage = (
            (len(matches) + len(partial_matches)) / len(our_species)
        ) * 100

        f.write(f"Exact matches: {exact_coverage:.2f}%\n")
        f.write(f"Genus-level matches: {genus_coverage:.2f}%\n")
        f.write(f"Total coverage: {total_coverage:.2f}%\n")
        f.write(f"No coverage: {100 - total_coverage:.2f}%\n\n")

        f.write("SUMMARY:\n")
        f.write("-" * 10 + "\n")
        f.write(f"✓ {len(matches)} species have exact BGC matches\n")
        f.write(f"~ {len(partial_matches)} species have genus-level matches\n")
        f.write(f"✗ {len(unmatched)} species require de novo BGC discovery\n")
        f.write(f"\nAnalysis completed on {len(our_species)} unique species.\n")

    print("Coverage statistics saved to: results/plantismash_coverage_stats.txt")


if __name__ == "__main__":
    analyze_coverage()
