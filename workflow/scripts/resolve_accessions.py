#!/usr/bin/env python3
import argparse
import subprocess
import time
import pandas as pd
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


def get_ncbi_api_key():
    """Get NCBI API key from environment variable or .env file"""
    # First try environment variable
    api_key = os.environ.get("NCBI_API_KEY")
    if api_key:
        return api_key

    # Try to load from .env file
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                for line in f:
                    if line.strip().startswith("NCBI_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
                        if api_key and api_key != "your_api_key_here":
                            return api_key
        except Exception:
            pass

    return None


def get_rate_limit_delay():
    """Get appropriate delay based on API key availability"""
    api_key = get_ncbi_api_key()
    if api_key:
        # With API key: 10 rps = 0.1 second delay
        return 0.1
    else:
        # Without API key: 5 rps = 0.2 second delay
        return 0.2


def run_cmd(cmd):
    """Run command and return result, handling errors gracefully"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        # Return the error result for analysis
        return e


def parse_datasets_output(output):
    """
    Parse the JSON lines output from datasets command to extract accession.
    """
    try:
        lines = output.strip().split("\n")
        for line in lines:
            if line.strip():
                data = json.loads(line)
                # Check for accession at top level first
                if "accession" in data:
                    return data["accession"]
                # Fallback to reports structure if it exists
                elif "reports" in data and data["reports"]:
                    accession = data["reports"][0].get("accession")
                    if accession:
                        return accession
    except (json.JSONDecodeError, KeyError, IndexError):
        pass
    return None


def parse_error_message(error_output):
    """
    Parse error messages from datasets command to determine the specific error type.
    Returns a descriptive status message.
    """
    error_output = error_output.strip()

    if "not recognized" in error_output:
        return "Invalid Taxonomy Name - Not Recognized"
    elif "not exact" in error_output:
        return "Taxonomy Name Not Exact - Suggestions Available"
    elif "valid, but no genome data is currently available" in error_output:
        return "Valid Taxonomy - No Genome Data Available"
    else:
        return "Error Querying Genome Database"


def search_ncbi_for_accession_with_details(search_term):
    """
    Search for genome accession using datasets summary genome taxon commands.
    Implements ranking system:
    1. Annotated reference genome
    2. Annotated genome (non-reference)
    3. Reference genome (not annotated)
    4. Genome (not annotated)

    Returns tuple: (accession, annotation_level, status_message, download_method)
    """
    # Get API key for rate limiting
    api_key = get_ncbi_api_key()

    # Level 1: Annotated reference genome
    annotated_ref_cmd = [
        "datasets",
        "summary",
        "genome",
        "taxon",
        search_term,
        "--reference",
        "--annotated",
        "--as-json-lines",
    ]

    if api_key:
        annotated_ref_cmd.extend(["--api-key", api_key])

    result = run_cmd(annotated_ref_cmd)
    if isinstance(result, subprocess.CalledProcessError):
        error_output = result.stderr.strip()
        error_status = parse_error_message(error_output)

        # If it's a taxonomy error, return immediately
        if "Invalid Taxonomy" in error_status or "Not Exact" in error_status:
            return None, None, error_status, None
    else:
        # Success - parse the JSON output
        accession = parse_datasets_output(result.stdout)
        if accession:
            return (
                accession,
                1,
                "Annotated Reference Genome Available",
                "datasets_download",
            )

    # Level 2: Annotated genome (non-reference)
    annotated_cmd = [
        "datasets",
        "summary",
        "genome",
        "taxon",
        search_term,
        "--annotated",
        "--as-json-lines",
    ]

    if api_key:
        annotated_cmd.extend(["--api-key", api_key])

    result = run_cmd(annotated_cmd)
    if isinstance(result, subprocess.CalledProcessError):
        error_output = result.stderr.strip()
        error_status = parse_error_message(error_output)

        # If it's a taxonomy error, return immediately
        if "Invalid Taxonomy" in error_status or "Not Exact" in error_status:
            return None, None, error_status, None
    else:
        # Success - parse the JSON output
        accession = parse_datasets_output(result.stdout)
        if accession:
            return (
                accession,
                2,
                "Annotated Genome Available (Non-Reference)",
                "datasets_download",
            )

    # Level 3: Reference genome (not annotated)
    reference_cmd = [
        "datasets",
        "summary",
        "genome",
        "taxon",
        search_term,
        "--reference",
        "--as-json-lines",
    ]

    if api_key:
        reference_cmd.extend(["--api-key", api_key])

    result = run_cmd(reference_cmd)
    if isinstance(result, subprocess.CalledProcessError):
        error_output = result.stderr.strip()
        error_status = parse_error_message(error_output)

        # If it's a taxonomy error, return immediately
        if "Invalid Taxonomy" in error_status or "Not Exact" in error_status:
            return None, None, error_status, None
    else:
        # Success - parse the JSON output
        accession = parse_datasets_output(result.stdout)
        if accession:
            return (
                accession,
                3,
                "Reference Genome Available (Not Annotated)",
                "datasets_download_genome_only",
            )

    # Level 4: Genome (not annotated)
    genome_cmd = [
        "datasets",
        "summary",
        "genome",
        "taxon",
        search_term,
        "--as-json-lines",
    ]

    if api_key:
        genome_cmd.extend(["--api-key", api_key])

    result = run_cmd(genome_cmd)
    if isinstance(result, subprocess.CalledProcessError):
        error_output = result.stderr.strip()
        error_status = parse_error_message(error_output)

        # If it's a taxonomy error, return immediately
        if "Invalid Taxonomy" in error_status or "Not Exact" in error_status:
            return None, None, error_status, None

        # If it's "no genome data" error, return that status
        if "No Genome Data Available" in error_status:
            return None, None, error_status, None

        # Other errors
        return None, None, error_status, None
    else:
        # Success - parse the JSON output
        accession = parse_datasets_output(result.stdout)
        if accession:
            return (
                accession,
                4,
                "Genome Available (Not Annotated)",
                "datasets_download_genome_only",
            )

    return None, None, "No Genome Data Available", None


def process_single_species(row, rate_limit_lock):
    """Process a single species row and return results"""
    search_priority = [
        ("Accepted name", row.get("Accepted name")),
        ("Legacy Name", row.get("Legacy Name")),
        ("Genus", row.get("Genus")),
    ]
    accession = None
    name_used = None
    priority_level = None
    annotation_level = None
    status_message = None
    download_method = None

    for priority, (label, term) in enumerate(search_priority, 1):
        if pd.notna(term) and str(term).strip():
            # Use rate limiting lock for thread safety
            with rate_limit_lock:
                time.sleep(get_rate_limit_delay())

            accession, annotation_level, status_message, download_method = (
                search_ncbi_for_accession_with_details(str(term).strip())
            )
            if accession:
                name_used = label
                priority_level = priority
                break

    if accession:
        return {
            "Accepted name": row.get("Accepted name"),
            "Status": status_message,
            "Accession": accession,
            "Name Used": name_used,
            "Priority Level": priority_level,
            "Annotation Level": annotation_level,
            "Download Method": download_method,
        }, accession
    else:
        return {
            "Accepted name": row.get("Accepted name"),
            "Status": status_message or "No Reference Proteome Found",
            "Accession": "N/A",
            "Name Used": "N/A",
            "Priority Level": "N/A",
            "Annotation Level": "N/A",
            "Download Method": "N/A",
        }, None


def main():
    parser = argparse.ArgumentParser(description="Resolve accessions for species list")
    parser.add_argument("--species", required=True, help="Input CSV with species names")
    parser.add_argument(
        "--status", required=True, help="Output CSV with per-species status"
    )
    parser.add_argument(
        "--accessions", required=True, help="Output TXT with one accession per line"
    )
    parser.add_argument(
        "--download-info",
        required=True,
        help="Output CSV with download method information",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Maximum number of parallel workers (default: 3)",
    )
    args = parser.parse_args()

    Path("results").mkdir(parents=True, exist_ok=True)
    Path("proteomes").mkdir(parents=True, exist_ok=True)

    species_df = pd.read_csv(args.species)
    required_cols = ["Accepted name", "Legacy Name", "Genus"]
    for col in required_cols:
        if col not in species_df.columns:
            raise ValueError(f"Missing required column: {col}")

    statuses = []
    accessions = []
    download_info = []

    # Create a lock for rate limiting
    rate_limit_lock = threading.Lock()

    # Process species in parallel
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # Submit all species for processing
        future_to_row = {
            executor.submit(process_single_species, row, rate_limit_lock): row
            for _, row in species_df.iterrows()
        }

        # Collect results as they complete
        for future in as_completed(future_to_row):
            status, accession = future.result()
            statuses.append(status)
            if accession:
                accessions.append(accession)
                # Add to download info if it has a valid download method
                if status.get("Download Method") and status["Download Method"] != "N/A":
                    download_info.append(
                        {
                            "Accession": accession,
                            "Annotation Level": status["Annotation Level"],
                            "Download Method": status["Download Method"],
                            "Species": status["Accepted name"],
                        }
                    )

    pd.DataFrame(statuses).to_csv(args.status, index=False)
    with open(args.accessions, "w") as f:
        for acc in accessions:
            f.write(f"{acc}\n")

    # Write download info for annotated genomes
    if download_info:
        pd.DataFrame(download_info).to_csv(args.download_info, index=False)
    else:
        # Create empty download_info.csv file if no annotated genomes found
        pd.DataFrame(
            columns=["Accession", "Annotation Level", "Download Method", "Species"]
        ).to_csv(args.download_info, index=False)


if __name__ == "__main__":
    main()
