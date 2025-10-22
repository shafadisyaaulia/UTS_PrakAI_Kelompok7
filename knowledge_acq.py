"""
modules/knowledge_acq.py – CRUD untuk akuisisi pengetahuan dari UI
Versi revisi: validasi ketat, hasil terstruktur, utilitas tambahan
"""

from typing import Dict, Any, List, Optional
from modules.utils import load_json, save_json
from modules.knowledge_base import validate_rule  # memeriksa struktur minimal: id, fase, if, then, cf

# -----------------------------
# Helper validation & utilities
# -----------------------------

def _cf_valid(cf: Any) -> bool:
    try:
        v = float(cf)
        return 0.0 <= v <= 1.0
    except Exception:
        return False

def _id_exists(rules: List[Dict[str, Any]], rule_id: str) -> bool:
    return any(r.get("id") == rule_id for r in rules)

def _normalize_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalisasi field wajib:
    - if -> list[str]
    - then -> str non-empty
    - cf -> float [0,1]
    - fase -> str (vegetatif/generatif), tidak dipaksa di sini
    """
    norm = dict(rule)  # shallow copy

    # Normalisasi 'if'
    if isinstance(norm.get("if"), str):
        norm["if"] = [norm["if"].strip()] if norm["if"].strip() else []
    elif isinstance(norm.get("if"), list):
        norm["if"] = [str(x).strip() for x in norm["if"] if str(x).strip()]
    else:
        norm["if"] = []

    # Normalisasi 'then'
    if "then" in norm and norm["then"] is not None:
        norm["then"] = str(norm["then"]).strip()

    # Normalisasi 'cf'
    if "cf" in norm:
        norm["cf"] = float(norm["cf"]) if _cf_valid(norm["cf"]) else norm.get("cf")

    # Normalisasi 'fase'
    if "fase" in norm and norm["fase"] is not None:
        norm["fase"] = str(norm["fase"]).strip().lower()

    return norm

def _validate_full(rule: Dict[str, Any]) -> Optional[str]:
    """
    Gabungan cek struktur + range CF + validator domain (validate_rule).
    Return None jika valid; string pesan error jika invalid.
    """
    rule = _normalize_rule(rule)

    if not isinstance(rule.get("id"), str) or not rule["id"].strip():
        return "ID rule wajib diisi (string non-empty)."

    for k in ("fase", "if", "then", "cf"):
        if k not in rule:
            return f"Field '{k}' wajib ada."

    if not isinstance(rule["if"], list) or any(not isinstance(x, str) or not x for x in rule["if"]):
        return "Field 'if' harus berupa list string dan tidak boleh kosong elemennya."
    if not isinstance(rule["then"], str) or not rule["then"]:
        return "Field 'then' harus berupa string dan tidak boleh kosong."
    if not _cf_valid(rule["cf"]):
        return "Nilai 'cf' harus angka antara 0 dan 1."

    # Validator domain (struktur minimal)
    if not validate_rule(rule):
        return "Rule tidak valid menurut validator knowledge_base."

    return None

# -----------------------------
# CRUD API (untuk di-UI)
# -----------------------------

def list_rules(path: str) -> Dict[str, Any]:
    rules = load_json(path)
    return {"status": "success", "msg": f"{len(rules)} rule ditemukan.", "data": rules}

def get_rule(path: str, rule_id: str) -> Dict[str, Any]:
    rules = load_json(path)
    for r in rules:
        if r.get("id") == rule_id:
            return {"status": "success", "msg": "Rule ditemukan.", "data": r}
    return {"status": "error", "msg": "Rule tidak ditemukan.", "data": None}

def add_rule(path: str, new_rule: Dict[str, Any]) -> Dict[str, Any]:
    rules = load_json(path)
    new_rule = _normalize_rule(new_rule)
    err = _validate_full(new_rule)
    if err:
        return {"status": "error", "msg": err, "data": None}
    if _id_exists(rules, new_rule["id"]):
        return {"status": "error", "msg": "ID rule sudah ada.", "data": None}

    rules.append(new_rule)
    save_json(rules, path)
    return {"status": "success", "msg": f"Rule {new_rule['id']} berhasil ditambahkan.", "data": new_rule}

def delete_rule(path: str, rule_id: str) -> Dict[str, Any]:
    rules = load_json(path)
    before = len(rules)
    updated = [r for r in rules if r.get("id") != rule_id]
    if len(updated) == before:
        return {"status": "error", "msg": "Rule tidak ditemukan.", "data": None}
    save_json(updated, path)
    return {"status": "success", "msg": f"Rule {rule_id} berhasil dihapus.", "data": None}

def edit_rule(path: str, rule_id: str, updated_rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update isi rule. Mengizinkan perubahan ID selama tidak bentrok.
    """
    rules = load_json(path)
    idx = next((i for i, r in enumerate(rules) if r.get("id") == rule_id), None)
    if idx is None:
        return {"status": "error", "msg": "Rule tidak ditemukan.", "data": None}

    updated_rule = _normalize_rule(updated_rule)
    err = _validate_full(updated_rule)
    if err:
        return {"status": "error", "msg": err, "data": None}

    new_id = updated_rule["id"]
    if new_id != rule_id and _id_exists(rules, new_id):
        return {"status": "error", "msg": f"Gagal ubah ID: {new_id} sudah dipakai.", "data": None}

    rules[idx] = updated_rule
    save_json(rules, path)
    return {"status": "success", "msg": f"Rule {rule_id} berhasil diperbarui.", "data": updated_rule}