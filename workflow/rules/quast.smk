# QUAST quality assessment rules for genome assemblies


rule rule_qc_quast:
    input:
        fasta="resources/genomes/{acc}.fna.gz",
    output:
        report_html="results/qc/quast/{acc}/report.html",
        report_tex="results/qc/quast/{acc}/report.tex",
        report_txt="results/qc/quast/{acc}/report.txt",
        report_pdf="results/qc/quast/{acc}/report.pdf",
        report_tsv="results/qc/quast/{acc}/report.tsv",
        transposed_report_tex="results/qc/quast/{acc}/transposed_report.tex",
        transposed_report_txt="results/qc/quast/{acc}/transposed_report.txt",
        transposed_report_tsv="results/qc/quast/{acc}/transposed_report.tsv",
        icarus="results/qc/quast/{acc}/icarus.html",
    wildcard_constraints:
        acc=r"(GCF|GCA)_\d+\.\d+",
    log:
        "logs/quast/{acc}.log",
    params:
        # QUAST parameters optimized for eukaryotic plant genomes
        extra="--eukaryote --min-contig 1000 --min-alignment 1000",
    threads: 10
    conda:
        "../envs/quast.yaml"
    message:
        "Running QUAST quality assessment for genome assembly: {wildcards.acc}"
    shell:
        """
        quast.py {input.fasta} \
            --threads {threads} \
            -o results/qc/quast/{wildcards.acc} \
            {params.extra} \
            > {log} 2>&1
        """


rule quast_complete:
    input:
        quast_reports=expand(
            "results/qc/quast/{acc}/report.html",
            acc=lambda wc: checkpoints.resolve_accessions.get().output.accessions,
        ),
    output:
        "results/qc/quast/.quast_complete",
    log:
        "logs/quast_complete.log",
    conda:
        "../envs/shell-tools.yaml"
    shell:
        """
        (touch {output}) &> {log}
        """
