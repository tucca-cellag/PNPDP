#!/bin/bash

# Test script for HPC Species Proteome and BLAST Analysis Pipeline
# Run from the project root directory

echo "🧪 Testing HPC Species Proteome and BLAST Analysis Pipeline"
echo "=========================================================="

# Check if we're in the right directory
if [ ! -f "workflow/Snakefile" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   (where workflow/Snakefile is located)"
    exit 1
fi

echo "📁 Test files created in .test/ directory:"
echo "   - config.yaml (test configuration)"
echo "   - species.csv (test species data)"
echo "   - amp.fasta (test antimicrobial peptides)"
echo ""

echo "🚀 Running test workflow..."
echo ""

# Activate conda environment
echo "🔧 Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate snakemake

# Set environment variable for config file
export SNAKEMAKE_CONFIG=".test/config.yaml"

# Run the workflow with test configuration
snakemake --workflow-profile ./profiles/test

echo ""
echo "✅ Test completed! Check results/ for final output files"
echo ""
echo "📊 Final outputs (results/ directory):"
echo "   - blast_results.tsv (raw BLASTp search results)"
echo "   - species_with_hits.csv (species with significant hits)"
echo "   - analysis_summary.txt (human-readable summary)"
echo ""
echo "📁 Intermediate files (resources/ directory):"
echo "   - species_status.csv (species resolution status)"
echo "   - accessions.txt (NCBI genome accessions)"
echo "   - download_info.csv (download information)"
echo "   - proteomes/ (downloaded proteome files)"
echo "   - blast_db/ (BLAST database files)"
echo "   - query_shards/ (split query files)"
echo "   - blast_results/ (individual BLAST results)"
echo ""
echo "📋 Logs are in logs/"
