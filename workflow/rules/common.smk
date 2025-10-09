def get_proteome_files(wildcards):
    """Get list of proteome files from unique accessions"""
    # Use checkpoint to ensure proper re-evaluation
    checkpoint_output = checkpoints.deduplicate_accessions.get().output.unique_accs
    with open(checkpoint_output, "r") as f:
        accessions = [line.strip() for line in f if line.strip()]
    return [f"resources/proteomes/{acc}.faa.gz" for acc in accessions]
