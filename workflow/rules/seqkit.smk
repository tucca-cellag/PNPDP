# SeqKit assembly statistics rules


rule seqkit_assembly_stats:
    """
    Calculate basic assembly statistics using SeqKit.
    SeqKit provides ultrafast sequence statistics and manipulation features.
    
    SeqKit is an ultrafast, cross-platform command-line utility for FASTA/Q 
    file manipulation, highly performant for compressed file operations.
    """
    input:
        genome="resources/genomes/{acc}.fna.gz",
    output:
        stats="results/qc/seqkit/{acc}.seqkit.stats.tsv",
    log:
        "logs/seqkit/{acc}.log",
    params:
        # Calculate extended statistics including N50, GC content, etc.
        extra="--all",
    conda:
        "../envs/seqkit.yaml"
    threads: 4
    message:
        "Running SeqKit stats on assembly {wildcards.acc} for initial QC"
    shell:
        """
        (echo "Starting SeqKit assembly statistics for {wildcards.acc}" && \
        mkdir -pv results/qc/seqkit/ && \
        seqkit stats \
            {input.genome} \
            {params.extra} \
            -T \
            > {output.stats} 2> {log} && \
        echo "SeqKit statistics completed for {wildcards.acc}") &> {log}
        """
