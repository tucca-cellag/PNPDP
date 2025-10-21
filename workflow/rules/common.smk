# Global variables and configuration
species_csv = config["species_csv"]
query_fasta = config["query_fasta"]
num_shards = int(config.get("num_shards", 8))
threads_per_blast = int(config.get("threads_per_blast", 8))
ncbi_api_key = os.environ.get("NCBI_API_KEY")


def get_proteome_files(wildcards):
    """Get list of proteome files from unique accessions"""
    # Use checkpoint to ensure proper re-evaluation
    checkpoint_output = checkpoints.deduplicate_accessions.get().output.unique_accs
    with open(checkpoint_output, "r") as f:
        accessions = [line.strip() for line in f if line.strip()]
    return [f"resources/proteomes/{acc}.faa.gz" for acc in accessions]
