"""Streamed reference lookup and variant representation helpers.

Compressed FASTA is read sequentially without retaining a whole chromosome.
No reference genome, dataset, method scores or model is bundled or downloaded.
"""

from __future__ import annotations

import gzip
import re
from collections.abc import Callable, Mapping
from pathlib import Path


DNA = frozenset("ACGT")
STANDARD_CHROMS = {f"chr{number}" for number in range(1, 23)} | {"chrX", "chrY"}
_VARIANT_ID = re.compile(
    r"^(?P<chrom>chr(?:[0-9]+|X|Y))_(?P<position>[1-9][0-9]*)_"
    r"(?P<ref>[ACGT]+)_(?P<alt>[ACGT]+)(?:_(?P<identifier>.+))?$"
)


def reverse_complement(allele: str) -> str:
    """Return the reverse complement of a supported DNA allele."""
    return allele.upper().translate(str.maketrans("ACGT", "TGCA"))[::-1]


def supported_allele(value: object) -> bool:
    allele = str(value or "").upper()
    return bool(allele) and set(allele) <= DNA


def parse_source_variant_id(value: object) -> dict[str, object] | None:
    """Parse the source ``chr_pos_ref_alt[_id]`` representation exactly."""
    match = _VARIANT_ID.fullmatch(str(value or "").strip())
    if not match:
        return None
    payload = match.groupdict()
    return {
        "chromosome": payload["chrom"],
        "position_1based": int(payload["position"]),
        "source_ref_allele": payload["ref"],
        "source_alt_allele": payload["alt"],
        "source_identifier": payload.get("identifier") or "",
    }


def read_reference_segments(
    fasta_gz: Path, requests: Mapping[str, Mapping[int, int]]
) -> dict[tuple[str, int], str]:
    """Read requested segments from gzip FASTA with bounded memory.

    ``requests`` maps a FASTA contig to 1-based starts and required lengths.
    A maximum-length request is sufficient for callers that need several
    prefixes at one coordinate.  The function makes one sequential pass and
    only retains incomplete requests that cross a FASTA line boundary.
    """
    targets = {
        chrom: sorted((int(position), int(length)) for position, length in values.items())
        for chrom, values in requests.items()
        if values
    }
    result: dict[tuple[str, int], str] = {}
    current_chrom: str | None = None
    current_targets: list[tuple[int, int]] = []
    target_index = 0
    position_1based = 1
    pending: list[tuple[int, int, str]] = []

    def flush_pending(sequence: str) -> None:
        nonlocal pending
        if not pending:
            return
        unresolved: list[tuple[int, int, str]] = []
        for start, remaining, prefix in pending:
            suffix = sequence[:remaining]
            value = prefix + suffix
            if len(value) == len(prefix) + remaining:
                result[(str(current_chrom), start)] = value
            else:
                unresolved.append((start, remaining - len(suffix), value))
        pending = unresolved

    with gzip.open(fasta_gz, "rt", encoding="ascii") as handle:
        for raw in handle:
            if raw.startswith(">"):
                current_chrom = raw[1:].split(None, 1)[0]
                current_targets = targets.get(current_chrom, [])
                target_index = 0
                position_1based = 1
                pending = []
                continue
            if not current_targets:
                continue
            sequence = raw.strip().upper()
            if not sequence:
                continue
            flush_pending(sequence)
            line_start = position_1based
            line_end = line_start + len(sequence) - 1
            while target_index < len(current_targets):
                start, length = current_targets[target_index]
                if start > line_end:
                    break
                target_index += 1
                if start < line_start:
                    continue
                offset = start - line_start
                fragment = sequence[offset : offset + length]
                if len(fragment) == length:
                    result[(str(current_chrom), start)] = fragment
                else:
                    pending.append((start, length - len(fragment), fragment))
            position_1based = line_end + 1
    return result


def normalize_variant(
    chromosome: str,
    position_1based: int,
    ref_allele: str,
    alt_allele: str,
    previous_base: Callable[[int], str],
) -> tuple[str, int, str, str]:
    """Trim shared bases and apply the existing indel left-shift rule.

    Callers must validate REF against their chosen reference sequence and verify
    chromosome, position and genome build before calling. This function does
    not compare the supplied REF with reference sequence. ``previous_base``
    supplies preceding bases for indel shifting only. The returned tuple does
    not certify reference agreement or a complete normalization standard.
    """
    ref = ref_allele.upper()
    alt = alt_allele.upper()
    position = int(position_1based)
    if not supported_allele(ref) or not supported_allele(alt) or ref == alt:
        raise ValueError("variant alleles must be distinct nonempty A/C/G/T strings")
    while len(ref) > 1 and len(alt) > 1 and ref[-1] == alt[-1]:
        ref, alt = ref[:-1], alt[:-1]
    while len(ref) > 1 and len(alt) > 1 and ref[0] == alt[0]:
        ref, alt = ref[1:], alt[1:]
        position += 1
    while len(ref) != len(alt) and position > 1:
        previous = previous_base(position - 1).upper()
        if len(previous) != 1 or ref[-1] != previous or alt[-1] != previous:
            break
        ref, alt = previous + ref[:-1], previous + alt[:-1]
        position -= 1
    return chromosome, position, ref, alt


def canonical_variant_id(
    chromosome: str, position_1based: int, ref_allele: str, alt_allele: str
) -> str:
    """Format ``chromosome:position:REF:ALT`` with uppercase alleles.

    This formatter does not validate genome build, reference alleles, chromosome
    naming, coordinate validity or biological equivalence.
    """
    return f"{chromosome}:{int(position_1based)}:{ref_allele.upper()}:{alt_allele.upper()}"
