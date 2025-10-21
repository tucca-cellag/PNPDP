# NCBI datasets download and extraction rules


rule datasets_download_genome_data:
    input:
        csv=species_csv,
    output:
        dataset_zip="resources/dataset_zips/{acc}.zip",
    wildcard_constraints:
        acc=r"(GCF|GCA)_\d+\.\d+",
    log:
        "logs/download/{acc}.log",
    params:
        api_key_flag=lambda wc, input, output: (
            f"--api-key {ncbi_api_key}" if ncbi_api_key else ""
        ),
    conda:
        "../envs/ncbi-datasets.yaml"
    message:
        "Downloading genome data package for NCBI accession: {wildcards.acc}"
    shell:
        """
        (echo "Starting download for {wildcards.acc}" && \
        mkdir -pv ./resources/dataset_zips/ && \
        echo "Downloading genome data package..." && \
        datasets download genome accession {wildcards.acc} \
            --include genome,gff3,gbff,cds,seq-report \
            --annotated \
            --no-progressbar \
            --debug \
            --filename {output.dataset_zip} \
            {params.api_key_flag} && \
        echo "Download completed for {wildcards.acc}") &> {log}
        """


rule extract_genome_data:
    input:
        dataset_zip="resources/dataset_zips/{acc}.zip",
    output:
        genome="resources/genomes/{acc}.fna.gz",
        gff3="resources/gff3/{acc}.gff3.gz",
        gbff="resources/gbff/{acc}.gbff.gz",
        cds="resources/cds/{acc}.cds.fna.gz",
        seq_report="resources/seq_reports/{acc}.seq_report.txt",
    wildcard_constraints:
        acc=r"(GCF|GCA)_\d+\.\d+",
    log:
        "logs/extract/{acc}.log",
    conda:
        "../envs/ncbi-datasets.yaml"
    message:
        "Extracting genome data for NCBI accession: {wildcards.acc}"
    shell:
        """
        (echo "Starting extraction for {wildcards.acc}" && \
        mkdir -pv ./resources/genomes/ ./resources/gff3/ ./resources/gbff/ ./resources/cds/ ./resources/seq_reports/ && \
        echo "Extracting genomic sequences..." && \
        unzip -p {input.dataset_zip} ncbi_dataset/data/{wildcards.acc}/genomic.fna | \
        gzip > {output.genome} && \
        echo "Extracting GFF3 annotation..." && \
        unzip -p {input.dataset_zip} ncbi_dataset/data/{wildcards.acc}/genomic.gff | \
        gzip > {output.gff3} && \
        echo "Extracting GenBank flat file..." && \
        unzip -p {input.dataset_zip} ncbi_dataset/data/{wildcards.acc}/genomic.gbff | \
        gzip > {output.gbff} && \
        echo "Extracting CDS sequences..." && \
        unzip -p {input.dataset_zip} ncbi_dataset/data/{wildcards.acc}/cds_from_genomic.fna | \
        gzip > {output.cds} && \
        echo "Extracting sequence report..." && \
        unzip -p {input.dataset_zip} ncbi_dataset/data/{wildcards.acc}/sequence_report.txt > {output.seq_report} && \
        echo "Extraction completed for {wildcards.acc}") &> {log}
        """


rule download_complete:
    input:
        genomes=expand(
            "resources/genomes/{acc}.fna.gz",
            acc=lambda wc: checkpoints.resolve_accessions.get().output.accessions,
        ),
    output:
        "resources/genomes/.download_complete",
    log:
        "logs/download_complete.log",
    conda:
        "../envs/shell-tools.yaml"
    shell:
        """
        (touch {output}) &> {log}
        """
