# HPC Species Proteome and BLAST Analysis Pipeline

This pipeline automates the process of checking for available proteomes for a list of species, downloading them, creating a local BLAST database, and running a BLASTp search against it using your query sequences.

## Prerequisites

- **Conda/Mamba**: Ensure you have Miniconda, Anaconda, or Mamba installed on your cluster user account.
- **Snakemake**: Install Snakemake in your base environment: `conda install snakemake` or `mamba install snakemake`
- **NCBI API Key** (recommended): Get a free API key from [NCBI Account Settings](https://www.ncbi.nlm.nih.gov/account/settings/) for enhanced access (10 requests per second vs. 5 rps without key).

The workflow will automatically create isolated conda environments for each rule using the environment definitions in `workflow/envs/`. No manual environment setup is required.

### Setting up NCBI API Key

To avoid rate limiting when querying NCBI databases, set up an API key:

1. **Get your API key**: Visit [NCBI Account Settings](https://www.ncbi.nlm.nih.gov/account/settings/) and create a free API key
2. **Create `.env` file**: Copy `env.example` to `.env` and add your API key:

   ```bash
   cp env.example .env
   # Edit .env and replace 'your_api_key_here' with your actual API key
   ```

3. **Alternative**: Set environment variable:

   ```bash
   export NCBI_API_KEY=your_actual_api_key_here
   ```

The pipeline will automatically use the API key if available, providing enhanced access at 10 requests per second (vs. 5 rps without key).

For detailed information about NCBI API keys, see the [official NCBI Datasets API documentation](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/api-keys/).

## Input File Preparation

### Converting Excel Files to CSV

If your species data is in an Excel file (.xlsx), you'll need to convert it to CSV format. The workflow expects a CSV file with these columns:

- `cell_line`: Unique identifier for each cell line/culture
- `Accepted name`: The accepted scientific name (used for NCBI queries)
- `Legacy Name`: Alternative/legacy name (backup for queries)
- `Genus`: Taxonomic genus

#### Method 1: Using the Standalone Script (Recommended)

```bash
# Install required dependency (if not already installed)
pip install openpyxl

# Run the conversion script
python convert_excel_to_csv.py your_file.xlsx species.csv
```

#### Method 2: Manual Python Commands

```bash
# Install required dependency (if not already installed)
pip install openpyxl

# Convert Excel to CSV with proper column mapping
python3 -c "
import pandas as pd

# Read the Excel file
df = pd.read_excel('your_file.xlsx')

# Create a simplified dataframe with the columns we need
species_df = pd.DataFrame({
    'cell_line': df['Culture ID'],  # Use Culture ID as cell line identifier
    'Accepted name': df['Accepted Name (link)'],
    'Legacy Name': df['Legacy Name'], 
    'Genus': df['Genus']
})

# Remove duplicates based on all taxonomic fields
species_df = species_df.drop_duplicates(subset=['Accepted name', 'Legacy Name', 'Genus'])

print(f'Created species CSV with {len(species_df)} unique species (duplicates removed based on Accepted name, Legacy Name, and Genus)')

# Clean up formatting (remove tabs and extra whitespace)
species_df['Genus'] = species_df['Genus'].str.strip().str.replace('\t', '')
species_df['Accepted name'] = species_df['Accepted name'].str.strip()
species_df['Legacy Name'] = species_df['Legacy Name'].str.strip()

# Save to CSV
species_df.to_csv('species.csv', index=False)
print('Saved to species.csv')
"
```

**Note**: Adjust the column names (`'Culture ID'`, `'Accepted Name (link)'`, etc.) to match your Excel file's actual column headers. The standalone script (`convert_excel_to_csv.py`) includes error checking and helpful output messages.

## File Structure

Organize your files in a single directory like this:

```text
/your/project/directory/
├-- species.csv              # Your input file with species names (CSV format)
├-- query_sequences.fasta    # Your input file with query sequences
├-- convert_excel_to_csv.py  # Excel to CSV conversion script (provided)
├-- env.example              # Environment variables template (provided)
├-- config/
│   └-- config.yaml         # Configuration file (provided)
├-- workflow/
│   ├-- Snakefile           # The main Snakemake workflow (provided)
│   ├-- envs/               # Conda environment definitions (provided)
│   └-- scripts/            # Helper scripts (provided)
├-- profiles/
│   └-- slurm/              # SLURM executor profile (provided)
│       └-- config.v8+.yaml # SLURM configuration (provided)
├-- resources/              # Intermediate files (created by workflow)
├-- results/                # Final outputs (created by workflow)
└-- logs/                   # Workflow logs (created by workflow)
```

## How to Run

### Prepare Your Input Files

- **species.csv**: This file must contain a header with these exact columns:
  - `cell_line`: Unique identifier for each cell line/culture
  - `Accepted name`: The accepted scientific name (used for NCBI queries)
  - `Legacy Name`: Alternative/legacy name (backup for queries)
  - `Genus`: Taxonomic genus
- **query_sequences.fasta**: This should be a standard FASTA file containing your query sequences (e.g., proteins, peptides, or any sequences you want to search against the species proteomes).

### Configure the Pipeline

Edit `config/config.yaml` to adjust:

- `species_csv`: Path to your species CSV file (default: "resources/species.csv")
- `query_fasta`: Path to your query sequences FASTA file (default: "resources/amp.fasta")
- `num_shards`: Number of query shards for parallel BLAST (default: 8)
- `threads_per_blast`: CPUs per BLAST job (default: 8)
- `resolve_accessions_threads`: Parallel workers for species resolution (default: 5)

### Run with Snakemake

From your project root directory, run:

```bash
snakemake --profile profiles/slurm
```

The workflow will:

- Automatically create conda environments for each rule
- Submit jobs to SLURM using your configured profile
- Run BLAST jobs in parallel across multiple nodes

### Running Interactively on HPC

To run the workflow interactively while ensuring it continues after 
disconnection, use one of these methods:

#### Method 1: Using `screen` (Recommended)

```bash
# Start a new screen session
screen -S snakemake_workflow

# Run the workflow
snakemake --profile profiles/slurm

# Detach from screen: Press Ctrl+A, then D
# To reattach later: screen -r snakemake_workflow
```

#### Method 2: Using `tmux`

```bash
# Start a new tmux session
tmux new-session -s snakemake_workflow

# Run the workflow
snakemake --profile profiles/slurm

# Detach from tmux: Press Ctrl+B, then D
# To reattach later: tmux attach-session -t snakemake_workflow
```

#### Method 3: Using `nohup` (Simple but less interactive)

```bash
# Run with nohup to prevent termination on disconnect
nohup snakemake --profile profiles/slurm > workflow.log 2>&1 &

# Monitor progress
tail -f workflow.log
```

#### Method 4: Submit as SLURM Job (Most Robust)

Create a job script `run_workflow.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=snakemake_workflow
#SBATCH --partition=batch
#SBATCH --account=your_account
#SBATCH --time=72:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=4

# Load modules if needed
module load conda

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate snakemake

# Run the workflow
snakemake --profile profiles/slurm
```

Then submit:

```bash
sbatch run_workflow.sh
```

**Recommendation**: Use Method 1 (screen) or Method 4 (SLURM job) for
long-running workflows. Screen allows interactive monitoring, while
SLURM jobs are more robust for very long runs.

### Customizing SLURM Resources

Edit `profiles/slurm/config.v8+.yaml` to adjust:

- `slurm_partition`: SLURM partition name (default: "batch")
- `slurm_account`: SLURM account name (default: "default")
- `runtime`: Job time limit in minutes (default: 4320)
- `mem_mb`: Memory per job in MB (default: 32000)
- `cpus_per_task`: CPUs per job (default: 12)
- `slurm_extra`: Additional SLURM flags (email notifications, etc.)
- `jobs`: Maximum concurrent jobs (default: 100)
- `latency_wait`: Wait time for files in seconds (default: 120)

## Output

The workflow will produce several output files in the results/ directory:

- **blast_results.tsv**: The raw, tab-separated output from the BLASTp search (outfmt 6).
- **species_with_hits.csv**: A list of species from your input that had at least one significant BLASTp hit against your query sequences.
- **analysis_summary.txt**: A human-readable summary of the key statistics from the analysis.

Additional intermediate files are created in the resources/ directory:

- **species_status.csv**: A log detailing which of your species had a reference proteome available for download on NCBI.
- **accessions.txt**: List of NCBI genome accessions for species with available proteomes.
- **download_info.csv**: Detailed download information for each species.
- **proteomes/**: Directory containing downloaded proteome files (compressed FASTA format).
- **blast_db/**: Directory containing the BLAST database files.
- **query_shards/**: Directory containing split query files for parallel processing.
- **blast_results/**: Directory containing individual BLAST result files (temporary).

This setup allows the entire job to run independently on the cluster, and you will be notified by email when it completes (if email notifications are configured in your SLURM profile).
