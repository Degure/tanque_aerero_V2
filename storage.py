# storage.py - Numeração automática e histórico de propostas
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTADOR_FILE = os.path.join(BASE_DIR, "contador_cotacao.json")
CONTADOR_LOCK = os.path.join(BASE_DIR, "contador_cotacao.lock")
HISTORICO_DIR = os.path.join(BASE_DIR, "historico_propostas")


def _garantir_pasta():
    os.makedirs(HISTORICO_DIR, exist_ok=True)


def _normalizar_numero(numero: str) -> str:
    return (numero or "").strip().upper()


def _path_json_cotacao(numero: str) -> str:
    seguro = "".join(c if c.isalnum() or c in "-_" else "_" for c in _normalizar_numero(numero))
    return os.path.join(HISTORICO_DIR, f"{seguro}.json")


def numero_existe(numero: str) -> bool:
    """True se já existe proposta salva com este número."""
    if not numero or not numero.strip():
        return False
    _garantir_pasta()
    path = _path_json_cotacao(numero)
    if os.path.exists(path):
        return True
    alvo = _normalizar_numero(numero)
    try:
        for nome in os.listdir(HISTORICO_DIR):
            if not nome.endswith(".json"):
                continue
            try:
                with open(os.path.join(HISTORICO_DIR, nome), "r", encoding="utf-8") as f:
                    reg = json.load(f)
                if _normalizar_numero(str(reg.get("numero", ""))) == alvo:
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _com_lock(timeout: float = 5.0):
    """Lock por arquivo para reduzir colisão entre processos."""
    class _Lock:
        def __enter__(self):
            _garantir_pasta()
            self.fd = None
            inicio = time.time()
            while True:
                try:
                    self.fd = os.open(CONTADOR_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.write(self.fd, str(os.getpid()).encode())
                    return self
                except FileExistsError:
                    if time.time() - inicio > timeout:
                        try:
                            os.remove(CONTADOR_LOCK)
                        except Exception:
                            pass
                        inicio = time.time()
                    time.sleep(0.05)
                except Exception:
                    return self

        def __exit__(self, *args):
            try:
                if self.fd is not None:
                    os.close(self.fd)
            except Exception:
                pass
            try:
                if os.path.exists(CONTADOR_LOCK):
                    os.remove(CONTADOR_LOCK)
            except Exception:
                pass

    return _Lock()


def proximo_numero_cotacao(ano: Optional[int] = None) -> str:
    """
    Gera próximo número AAAA-NNNN.
    Usa lock e pula números já existentes no histórico.
    """
    if ano is None:
        ano = datetime.now().year

    with _com_lock():
        data = {"ano": ano, "seq": 0}
        if os.path.exists(CONTADOR_FILE):
            try:
                with open(CONTADOR_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        if data.get("ano") != ano:
            data = {"ano": ano, "seq": 0}

        for _ in range(10000):
            data["seq"] = int(data.get("seq", 0)) + 1
            candidato = f"{ano}-{data['seq']:04d}"
            if not numero_existe(candidato):
                break
        else:
            candidato = f"{ano}-{int(time.time()) % 100000:05d}"

        try:
            with open(CONTADOR_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return candidato


def salvar_proposta(
    numero: str,
    payload: Dict[str, Any],
    pdf_bytes: Optional[bytes] = None,
    sobrescrever: bool = False,
) -> str:
    """
    Salva proposta. Por padrão recusa se o número já existir.
    """
    _garantir_pasta()
    numero = (numero or "").strip()
    if not numero:
        raise ValueError("Número de cotação vazio.")

    if not sobrescrever and numero_existe(numero):
        raise FileExistsError(
            f"Já existe proposta com o número {numero}. "
            "Gere um novo número antes de salvar."
        )

    json_path = _path_json_cotacao(numero)
    registro = {
        "salvo_em": datetime.now().isoformat(timespec="seconds"),
        "numero": numero,
        "dados": payload,
    }
    tmp_path = json_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2, default=str)
    os.replace(tmp_path, json_path)

    if pdf_bytes:
        pdf_path = json_path[:-5] + ".pdf"
        tmp_pdf = pdf_path + ".tmp"
        with open(tmp_pdf, "wb") as f:
            f.write(pdf_bytes)
        os.replace(tmp_pdf, pdf_path)
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
