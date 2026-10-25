"""Завдання 2: Фільтр та аналізатор журналів DNS-запитів (Варіант 8)."""

import argparse
import csv
import logging
import re
import sys
from collections import Counter
from pathlib import Path

# Налаштування логера за вимогами методички
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger("DNS_Analyzer")


def load_blacklist(blacklist_path: Path) -> set[str]:
    """Зчитує чорний список доменів у множину для швидкої перевірки."""
    blacklist = set()
    if not blacklist_path.exists():
        logger.warning("Файл чорного списку не знайдено: %s", blacklist_path)
        return blacklist

    with blacklist_path.open("r", encoding="utf-8") as f:
        for line in f:
            domain = line.strip().lower()
            if domain and not domain.startswith("#"):
                blacklist.add(domain)
    return blacklist


def is_suspicious_domain(domain: str, min_domain_len: int) -> tuple[bool, str]:
    """Перевіряє домен на ознаки DGA, довжину або підозрілі зони TLD."""
    # 1. Занадто довгий домен (тунелювання або ексфільтрація)
    if len(domain) >= min_domain_len:
        return True, f"Abnormally long domain (Length: {len(domain)})"

    # 2. Небезпечні доменні зони верхнього рівня
    suspicious_tld_pattern = r"\.(xyz|top|ru|cc|tk|buzz|bid)$"
    if re.search(suspicious_tld_pattern, domain.lower()):
        return True, "Suspicious top-level domain (TLD)"

    # 3. Випадковий набір цифр і літер (евристика DGA)
    subdomains = domain.split(".")
    for sub in subdomains:
        has_digit = bool(re.search(r"\d", sub))
        has_alpha = bool(re.search(r"[a-z]", sub))
        if len(sub) > 10 and has_digit and has_alpha:
            return True, f"High entropy / suspicious subdomain: {sub}"

    return False, ""


def analyze_dns_log(
    log_file: Path,
    blacklist_file: Path,
    output_csv: Path,
    min_domain_len: int = 30,
) -> None:
    """Головна логіка фільтрації та аналізу DNS-журналу."""
    logger.info("Parsing DNS log file %s...", log_file)

    if not log_file.exists():
        logger.error("Файл DNS-логу не знайдено: %s", log_file)
        sys.exit(1)

    blacklist = load_blacklist(blacklist_file)
    query_counter: Counter = Counter()
    suspicious_records: list[dict] = []
    total_records = 0

    with log_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            reader.fieldnames = [fn.strip() for fn in reader.fieldnames]

        for row in reader:
            total_records += 1
            timestamp = row.get("Timestamp", "").strip()
            client_ip = row.get("ClientIP", "").strip()
            domain = row.get("Domain", "").strip()
            q_type = row.get("QueryType", "").strip().upper()

            query_counter[q_type] += 1

            # Перевірка 1: чорний список
            if domain.lower() in blacklist:
                suspicious_records.append(
                    {
                        "Timestamp": timestamp,
                        "ClientIP": client_ip,
                        "Domain": domain,
                        "QueryType": q_type,
                        "Reason": "Blacklisted domain match",
                    }
                )
                logger.warning(
                    "[BLACKMATCH] Client %s queried blacklisted domain: %s",
                    client_ip,
                    domain,
                )
                continue

            # Перевірка 2: DGA / аномальна довжина
            is_susp, reason = is_suspicious_domain(domain, min_domain_len)
            if is_susp:
                suspicious_records.append(
                    {
                        "Timestamp": timestamp,
                        "ClientIP": client_ip,
                        "Domain": domain,
                        "QueryType": q_type,
                        "Reason": reason,
                    }
                )
                logger.warning(
                    "[DGA-DETECT] %s: %s (Client: %s)",
                    reason,
                    domain,
                    client_ip,
                )

    logger.info("Processed %d DNS query records.", total_records)

    # Вивід статистики за типами запитів
    print("\n=== Query Type Breakdown ===")
    for q_name, count in query_counter.most_common():
        pct = (count / total_records * 100) if total_records > 0 else 0
        print(f"{q_name:<6}: {count} ({pct:.1f}%)")

    # Збереження результатів у CSV
    if suspicious_records:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open("w", newline="", encoding="utf-8") as out_f:
            fieldnames = [
                "Timestamp",
                "ClientIP",
                "Domain",
                "QueryType",
                "Reason",
            ]
            writer = csv.DictWriter(out_f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(suspicious_records)

        logger.info("Suspicious records exported to %s", output_csv)
    else:
        logger.info("Аномальних DNS-запитів не виявлено.")


def main() -> None:
    """Розбір аргументів командного рядка утиліти."""
    parser = argparse.ArgumentParser(
        description="Фільтр та аналізатор журналів DNS-запитів (Варіант 8)"
    )
    parser.add_argument(
        "--dns-log",
        type=Path,
        required=True,
        help="Шлях до вхідного файлу dns_queries.csv",
    )
    parser.add_argument(
        "--blacklist",
        type=Path,
        default=Path("labs/lab02/data/blacklist.txt"),
        help="Шлях до файлу з чорним списком доменів",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=Path("labs/lab02/data/dns_alerts.csv"),
        help="Шлях до вихідного CSV-файлу зі знайденими загрозами",
    )
    parser.add_argument(
        "--min-domain-len",
        type=int,
        default=30,
        help="Мінімальна довжина підозрілого домену",
    )

    args = parser.parse_args()
    analyze_dns_log(
        log_file=args.dns_log,
        blacklist_file=args.blacklist,
        output_csv=args.out_csv,
        min_domain_len=args.min_domain_len,
    )


if __name__ == "__main__":
    main()
