# BLAST database creation and search rules


rule concat_proteomes:
    input:
        proteomes=get_proteome_files,
    output:
        fasta="resources/blast_db/all_species_proteomes.faa",
        done="resources/blast_db/.concat_done",
    log:
        "logs/concat_proteomes.log",
    params:
        num_files=lambda wc, input, output: len(input.proteomes),
    conda:
        "../envs/shell-tools.yaml"
    shell:
        """
        (echo "Starting proteome concatenation..." && \
        mkdir -p "resources/blast_db" && \
        echo "Concatenating {params.num_files} proteome files..." && \
        for proteome in {input.proteomes}; do \
            echo "Processing: $proteome" && \
            gunzip -c "$proteome" >> {output.fasta}; \
        done && \
        echo "Creating completion flag..." && \
        touch {output.done} && \
        echo "Proteome concatenation completed") 2> {log}
        """


rule makeblastdb:
    input:
        fasta="resources/blast_db/all_species_proteomes.faa",
    output:
        multiext(
            "resources/blast_db/species_db",
            ".pdb",
            ".phr",
            ".pin",
            ".pot",
            ".psq",
            ".ptf",
            ".pto",
        ),
    log:
        "logs/makeblastdb.log",
    params:
        dbtitle="Custom Species Proteome Database",
        tmpdir=lambda wc, input, output: os.environ.get("TMPDIR", "tmp"),
        max_file_size=lambda wc, input, output: config.get(
            "makeblastdb_max_file_size", "4GB"
        ),
    conda:
        "../envs/shell-tools.yaml"
    shell:
        """
        (echo "Starting makeblastdb" && \
        echo "Purging modules and loading BLAST..." && \
        module purge && \
        module load blast/2.17.0 && \
        echo "Input FASTA: {input.fasta}" && \
        echo "TMPDIR: {params.tmpdir}" && \
        export TMPDIR={params.tmpdir} && \
        # Ensure sufficient virtual memory address space for BLAST v5 LMDB
        ulimit -v unlimited || true && \
        makeblastdb -in {input.fasta} -dbtype prot -out resources/blast_db/species_db \
            -input_type fasta -blastdb_version 5 -parse_seqids -title "{params.dbtitle}" \
            -max_file_sz {params.max_file_size} && \
        echo "makeblastdb completed") &> {log}
        """


rule blastp:
    input:
        shard=f"resources/query_shards/shard_{{i}}.faa",
        dbpin=f"resources/blast_db/species_db.pin",
    output:
        tsv=temp(f"resources/blast_results/shard_{{i}}.tsv"),
    log:
        f"logs/blastp/shard_{{i}}.log",
    threads: threads_per_blast
    params:
        blast_db_dir=lambda wc, input, output: os.path.dirname(input.dbpin),
    conda:
        "../envs/shell-tools.yaml"
    shell:
        """
        (echo "Starting BLAST search for shard {wildcards.i}" && \
        echo "Purging modules and loading BLAST..." && \
        module purge && \
        module load blast/2.17.0 && \
        echo "Query file: {input.shard}" && \
        echo "Database: {params.blast_db_dir}/species_db" && \
        echo "Output file: {output.tsv}" && \
        blastp -query {input.shard} -db {params.blast_db_dir}/species_db \
            -out {output.tsv} -outfmt '6 qseqid sseqid pident length mismatch \
            gapopen qstart qend sstart send evalue bitscore stitle' \
            -evalue 1e-5 -num_threads {threads} && \
        echo "BLAST search completed for shard {wildcards.i}") 2> {log}
        """
