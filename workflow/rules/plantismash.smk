# PlantiSMASH-specific rules


rule plantismash_download_databases:
    input:
        plantismash_dir="workflow/scripts/plantismash",
    output:
        done="resources/plantismash_databases/.download_done",
    log:
        "logs/plantismash_download.log",
    conda:
        "../envs/plantismash.yaml"
    shell:
        """
        (echo "Starting plantiSMASH database download..." && \
        mkdir -pv resources/plantismash_databases && \
        cd workflow/scripts/plantismash && \
        python download_databases.py && \
        echo "Creating completion flag..." && \
        touch ../../../resources/plantismash_databases/.download_done && \
        echo "plantiSMASH database download completed") 2> {log}
        """


rule plantismash_analysis:
    input:
        genome="resources/genomes/{acc}.gbff",
        databases="resources/plantismash_databases/.download_done",
        plantismash_dir="workflow/scripts/plantismash",
    output:
        results_dir="results/plantismash/{acc}",
    wildcard_constraints:
        acc=r"(GCF|GCA)_\d+\.\d+",
    log:
        "logs/plantismash/{acc}.log",
    threads: lambda wc, input: int(config.get("plantismash_threads", 4))
    conda:
        "../envs/plantismash.yaml"
    message:
        "Running plantiSMASH analysis for genome: {wildcards.acc}"
    shell:
        """
        (echo "Starting plantiSMASH analysis for {wildcards.acc}" && \
        mkdir -pv results/plantismash/{wildcards.acc} && \
        cd workflow/scripts/plantismash && \
        python run_antismash.py \
            --clusterblast \
            --knownclusterblast \
            --verbose \
            --debug \
            --limit -1 \
            --taxon plants \
            --cpus {threads} \
            --outputfolder ../../../results/plantismash/{wildcards.acc} \
            ../../../resources/genomes/{wildcards.acc}.gbff && \
        echo "plantiSMASH analysis completed for {wildcards.acc}") 2> {log}
        """
