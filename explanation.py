"""
modules/explanation.py - Modul penjelasan proses inferensi.
Menjelaskan HOW (bagaimana) dan WHY (mengapa) keputusan sistem dibuat berdasarkan aturan dan CF.
"""

from modules.certainty_factor import combine_cf

def _format_conditions(conditions):
    if not conditions:
        return "-"
    if len(conditions) == 1:
        return conditions[0]
    if len(conditions) == 2:
        return f"{conditions[0]} dan {conditions[1]}"
    return ", ".join(conditions[:-1]) + f", dan {conditions[-1]}"

def generate_explanation(trace):
    if not trace:
        return "Tidak ada aturan yang terpenuhi."

    teks = ["Sistem mengaktifkan aturan berikut:"]
    aggregated_cf = {}
    justification = {}

    for rule in trace:
        kondisi = rule.get("if", [])
        rekomendasi = rule.get("then", "Tidak diketahui")
        cf_rule = float(rule.get("cf", 0))

        teks.append(
            f"  - Rule {rule.get('id', '?')}: Jika {_format_conditions(kondisi)} "
            f"maka {rekomendasi} (CF rule {cf_rule:.2f})"
        )

        before_cf = aggregated_cf.get(rekomendasi, 0.0)
        combined_cf = combine_cf(before_cf, cf_rule)
        aggregated_cf[rekomendasi] = combined_cf

        justification.setdefault(rekomendasi, []).append(
            {
                "rule_id": rule.get("id", "?"),
                "conditions": kondisi,
                "rule_cf": cf_rule,
                "combined_cf": combined_cf,
            }
        )

    teks.append("")

    best_recommendation = max(aggregated_cf, key=aggregated_cf.get)
    best_cf = aggregated_cf[best_recommendation]
    detail_cf = justification[best_recommendation]
    kondisi_pendukung = sorted(
        {cond for item in detail_cf for cond in item["conditions"]}
    )

    teks.append("HOW:")
    teks.append(
        "Sistem menggabungkan nilai kepastian setiap rule yang aktif menggunakan "
        "metode Certainty Factor (CF)."
    )
    for item in detail_cf:
        teks.append(
            f"  - Setelah rule {item['rule_id']} dipertimbangkan, CF rekomendasi "
            f"menjadi {item['combined_cf']:.2f}."
        )
    teks.append(
        f"  - Rekomendasi akhir dipilih karena {best_recommendation} memiliki nilai CF tertinggi "
        f"{best_cf:.2f}."
    )

    teks.append("")
    teks.append("WHY:")
    teks.append(
        f"Gejala yang Anda berikan memenuhi kondisi {_format_conditions(kondisi_pendukung)}, "
        f"sehingga aturan yang mengarah pada rekomendasi '{best_recommendation}' aktif "
        "dan dipercaya."
    )

    return "\n".join(teks)