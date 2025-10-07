# Test Directory for HPC Species Proteome and BLAST Analysis Pipeline

This directory contains test files and scripts to validate the workflow
functionality with minimal test data.

## Prerequisites

- **Conda/Mamba**: Ensure you have Miniconda, Anaconda, or Mamba installed
- **Snakemake**: Install Snakemake in your base environment:
  `conda install snakemake` or `mamba install snakemake`
- **NCBI API Key** (recommended): Get a free API key from
  [NCBI Account Settings](https://www.ncbi.nlm.nih.gov/account/settings/)
  for enhanced access

## Test Files

- **`config.yaml`** - Test configuration with minimal settings
- **`species.csv`** - Test species data (Human and Mouse)
- **`amp.fasta`** - Test query sequences for BLAST analysis
- **`run_test.sh`** - Executable script to run the complete test

## Test Species

The test includes two species for validation:

- **Homo_sapiens** (Human)
- **Mus_musculus** (Mouse)

## How to Run Tests

### Option 1: Use the test script (recommended)

```bash
# From project root directory
./.test/run_test.sh
```

### Option 2: Manual Snakemake command

```bash
# From project root directory
snakemake --configfile .test/config.yaml --cores 4 --use-conda
```

### Option 3: Test specific rules

```bash
# Test species resolution only
snakemake --configfile .test/config.yaml resolve_species --cores 4 --use-conda

# Test BLAST database creation only
snakemake --configfile .test/config.yaml create_blast_db --cores 4 --use-conda
```

## Expected Outputs

After running the test, you should see these files in the results/ directory:

- **blast_results.tsv**: The raw, tab-separated output from the BLASTp search
- **species_with_hits.csv**: Species that had significant BLASTp hits
- **analysis_summary.txt**: Human-readable summary of key statistics

Additional intermediate files are created in the resources/ directory:

- **species_status.csv**: Log of which species had reference proteomes available
- **accessions.txt**: List of NCBI genome accessions for available proteomes
- **download_info.csv**: Detailed download information for each species
- **proteomes/**: Directory containing downloaded proteome files (compressed)
- **blast_db/**: Directory containing the BLAST database files
- **query_shards/**: Directory containing split query files for parallel processing
- **blast_results/**: Directory containing individual BLAST result files

## Cleanup

To clean up test results:

```bash
rm -rf results/ resources/ proteomes/ blast_db/ logs/
```
