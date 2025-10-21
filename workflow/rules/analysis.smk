# Analysis and aggregation rules


rule aggregate:
    input:
        shards=expand(f"resources/blast_results/shard_{{i}}.tsv", i=range(num_shards)),
        status="resources/species_status.csv",
    output:
        results="results/blast_results.tsv",
        hits="results/species_with_hits.csv",
        summary="results/analysis_summary.txt",
    log:
        "logs/aggregate.log",
    params:
        length=len({input.shards}),
    conda:
        "../envs/py.yaml"
    shell:
        """
        (echo "Starting result aggregation..." && \
        echo "Concatenating {params.length} BLAST result files..." && \
        cat {input.shards} > {output.results} && \
        echo "Running analysis script..." && \
        python workflow/scripts/analyze.py \
            --status {input.status} --blast {output.results} \
            --summary {output.summary} --hits {output.hits} && \
        echo "Analysis completed successfully") 2> {log}
        """


# Generate species names file for plantiSMASH coverage analysis
rule generate_species_names:
    input:
        species_csv=species_csv,
    output:
        species_names="species_names.txt",
    log:
        "logs/generate_species_names.log",
    conda:
        "../envs/py.yaml"
    message:
        "Generating species names file from species.csv"
    shell:
        """
        (echo "Starting species names generation..." && \
        python workflow/scripts/generate_species_names.py {input.species_csv} {output.species_names} && \
        echo "Species names file generated successfully") 2> {log}
        """


# PlantiSMASH coverage analysis
rule plantismash_coverage_analysis:
    input:
        species_csv=species_csv,
        species_names="species_names.txt",
    output:
        coverage_csv="results/plantismash_coverage_analysis.csv",
        coverage_stats="results/plantismash_coverage_stats.txt",
    log:
        "logs/plantismash_coverage.log",
    conda:
        "../envs/py.yaml"
    message:
        "Analyzing coverage of species against plantiSMASH pre-calculated BGCs"
    shell:
        """
        (echo "Starting plantiSMASH coverage analysis..." && \
        python workflow/scripts/analyze_plantismash_coverage.py && \
        echo "Coverage analysis completed") 2> {log}
        """
