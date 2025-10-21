# Data preparation rules
# Includes query splitting, accession resolution, and deduplication


checkpoint resolve_accessions:
    input:
        csv=species_csv,
    output:
        status="resources/species_status.csv",
        accessions="resources/accessions.txt",
        download_info="resources/download_info.csv",
    log:
        "logs/resolve_accessions.log",
    threads: lambda wc, input: int(config.get("resolve_accessions_threads", 3))
    conda:
        "../envs/ncbi-datasets.yaml"
    shell:
        """
        (set -Eeuo pipefail; \
        echo "[$(date -Is)] Starting resolve_accessions"; \
        echo "Host: $(hostname)"; \
        echo "Species CSV: {input.csv}"; \
        echo "Status out: {output.status}"; \
        echo "Accessions out: {output.accessions}"; \
        echo "Download info out: {output.download_info}"; \
        echo "Threads: {threads}"; \
        PYTHONUNBUFFERED=1 python -u workflow/scripts/resolve_accessions.py \
        --species {input.csv} \
        --status {output.status} \
        --accessions {output.accessions} \
        --download-info {output.download_info} \
        --max-workers {threads}; \
        echo "[$(date -Is)] Finished resolve_accessions") &> {log}
        """


checkpoint deduplicate_accessions:
    input:
        accs="resources/accessions.txt",
    output:
        unique_accs="resources/unique_accessions.txt",
    log:
        "logs/deduplicate_accessions.log",
    conda:
        "../envs/shell-tools.yaml"
    shell:
        """
        (echo "Starting accession deduplication..." && \
        echo "Input accessions: $(wc -l < {input.accs})" && \
        sort {input.accs} | uniq > {output.unique_accs} && \
        echo "Unique accessions: $(wc -l < {output.unique_accs})" && \
        echo "Deduplication completed") 2> {log}
        """
