# Split description

The benchmark split is defined at `unified_locus_id` level. A locus and all candidate relations belonging to it must remain in one split; no variant, gene or assay-derived row may move a shared locus across development and held-out partitions. The split is frozen before confirmatory truth access and is not rebalanced by outcome, score, distance, disease, cell type or comparator availability.

Use explicit development, held-out and excluded assignments for the selected application. Excluded/seen loci remain excluded and are not silently returned to the denominator. Any future split manifest must carry the contract version, source file hash, row counts, assignment algorithm and deterministic seed.

