#!/usr/bin/env python3
"""
Aggregate and analyze BLAST results from proteome searches.

This script processes BLAST results from proteome searches against species
genomes and generates summary statistics. It counts species with proteomes
available, species with BLAST hits, and unique proteins with hits. The
script outputs a summary report and a list of species that had successful
BLAST matches for further analysis.
"""
import argparse
import os
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate BLAST results and summarize"
    )
    parser.add_argument("--status", required=True, help="species_status.csv")
    parser.add_argument("--blast", required=True, help="concatenated blast_results.tsv")
    parser.add_argument("--summary", required=True, help="output summary path")
    parser.add_argument("--hits", required=True, help="output species_with_hits.csv")
    args = parser.parse_args()

    total_species = len(pd.read_csv(args.status))

    if not os.path.exists(args.blast) or os.path.getsize(args.blast) == 0:
        num_species_with_hits = 0
        num_unique_proteins_with_hits = 0
        species_with_hits = pd.DataFrame([{"Accepted name": s} for s in []])
    else:
        cols = [
            "query_id",
            "subject_id",
            "identity",
            "aln_length",
            "mismatches",
            "gap_opens",
            "q_start",
            "q_end",
            "s_start",
            "s_end",
            "evalue",
            "bitscore",
            "subject_title",
        ]
        df = pd.read_csv(args.blast, sep="\t", header=None, names=cols)
        df["species_name"] = (
            df["subject_title"].str.extract(r"\[(.*?)\]").fillna("Unknown")
        )

        # Count unique species with hits
        num_species_with_hits = df[df["species_name"] != "Unknown"][
            "species_name"
        ].nunique()

        # Count unique proteins (query sequences) with hits
        num_unique_proteins_with_hits = df["query_id"].nunique()

        species_with_hits = pd.DataFrame(
            df["species_name"].unique(), columns=["Accepted name"]
        )

    status_df = pd.read_csv(args.status)
    # Count species that have proteomes available
    # This includes species with annotated genomes OR those downloaded with datasets_download method
    proteomes_downloaded = len(
        status_df[(status_df["Download Method"] == "datasets_download")]
    )

    summary = (
        f"--- Analysis Summary ---\n"
        f"1. Total Species in Input: {total_species}\n"
        f"2. Species with a Reference Proteome Found: {proteomes_downloaded} "
        f"({proteomes_downloaded/total_species:.2%})\n"
        f"3. Species with at least one BLASTp Hit: {num_species_with_hits}\n"
        f"4. Unique Proteins with BLASTp Hits: {num_unique_proteins_with_hits}\n"
    )

    with open(args.summary, "w") as f:
        f.write(summary)

    species_with_hits.to_csv(args.hits, index=False)


if __name__ == "__main__":
    main()
