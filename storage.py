# storage.py - Numeração automática e histórico de propostas
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTADOR_FILE = os.path.join(BASE_DIR, "contador_cotacao.json")
HISTORICO_DIR = os.path.join(BASE_DIR, "historico_propostas")


def _garantir_pasta():
    os.makedirs(HISTORICO_DIR, exist_ok=True)


def proximo_numero_cotacao(ano: Optional[int] = None) -> str:
    """
    Gera próximo número no formato AAAA-NNNN (ex: 2026-0001).
    Incrementa e grava em contador_cotacao.json.
    """
    if ano is None:
        ano = datetime.now().year
    data = {"ano": ano, "seq": 0}
    if os.path.exists(CONTADOR_FILE):
        try:
            with open(CONTADOR_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    if data.get("ano") != ano:
        data = {"ano": ano, "seq": 0}
    data["seq"] = int(data.get("seq", 0)) + 1
    try:
        with open(CONTADOR_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return f"{ano}-{data['seq']:04d}"


def salvar_proposta(numero: str, payload: Dict[str, Any], pdf_bytes: Optional[bytes] = None) -> str:
    """
    Salva JSON da proposta e, se houver, o PDF.
    Retorna o caminho do JSON.
    """
    _garantir_pasta()
    seguro = "".join(c if c.isalnum() or c in "-_" else "_" for c in numero)
    json_path = os.path.join(HISTORICO_DIR, f"{seguro}.json")
    registro = {
        "salvo_em": datetime.now().isoformat(timespec="seconds"),
        "numero": numero,
        "dados": payload,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2, default=str)
    if pdf_bytes:
        pdf_path = os.path.join(HISTORICO_DIR, f"{seguro}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
    return json_path


def listar_propostas() -> List[Dict[str, Any]]:
    """Lista propostas salvas (mais recentes primeiro)."""
    _garantir_pasta()
    itens = []
    for nome in os.listdir(HISTORICO_DIR):
        if not nome.endswith(".json"):
            continue
        path = os.path.join(HISTORICO_DIR, nome)
        try:
            with open(path, "r", encoding="utf-8") as f:
                reg = json.load(f)
            dados = reg.get("dados") or {}
            cliente = (dados.get("cliente") or {}).get("razao_social", "—")
            itens.append({
                "numero": reg.get("numero", nome.replace(".json", "")),
                "salvo_em": reg.get("salvo_em", ""),
                "cliente": cliente,
                "total": dados.get("total_produtos", 0),
                "path": path,
            })
        except Exception:
            continue
    itens.sort(key=lambda x: x.get("salvo_em", ""), reverse=True)
    return itens


def carregar_proposta(path: str) -> Optional[Dict[str, Any]]:
    """Carrega o dict 'dados' de uma proposta salva."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            reg = json.load(f)
        return reg.get("dados")
    except Exception:
        return None
