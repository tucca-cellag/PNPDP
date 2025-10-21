# SeqFu2 assembly statistics rules


rule seqfu_assembly_stats:
    """
    Calculate comprehensive assembly statistics using SeqFu2.
    SeqFu provides core metrics like N50 and is optimized for FASTA/Q files.
    
    SeqFu2 is a high-performance utility designed to robustly and reproducibly 
    manipulate sequence files, supporting gzipped input files.
    """
    input:
        genome="resources/genomes/{acc}.fna.gz",
    output:
        # Output in standardized tabular format for Phase 5 Data Integration
        stats="results/qc/seqfu/{acc}.seqfu.stats.tsv",
    log:
        "logs/seqfu/{acc}.log",
    params:
        extra="--tsv",
    conda:
        "../envs/seqfu.yaml"
    threads: 1
    message:
        "Running SeqFu2 stats on assembly {wildcards.acc} for initial QC"
    shell:
        """
        (echo "Starting SeqFu2 assembly statistics for {wildcards.acc}" && \
        mkdir -pv results/qc/seqfu/ && \
        seqfu stats \
            {input.genome} \
            {params.extra} \
            > {output.stats} 2> {log} && \
        echo "SeqFu2 statistics completed for {wildcards.acc}") &> {log}
        """
