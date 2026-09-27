"""Testes do ciclo de autocoleta (boot) e do módulo iniciar_autocoleta."""

import pytest

import app as app_mod


@pytest.fixture(autouse=True)
def _reset_status():
    """Garante que o status global começa limpo entre testes."""
    from database import status
    from threading import Lock
    with Lock():
        status._estado.update(
            estado="ocioso",
            etapa=None,
            repo_atual=None,
            repos_concluidos=0,
            total_repos=0,
            mensagem="Coleta ainda não iniciada.",
        )


def test_autocoleta_coleta_pendentes(monkeypatch):
    """Quando há repositórios pendentes, inicia thread de coleta."""
    feita = False
    chamadas = []

    def fake_repositorios_pendentes():
        return [7]

    def fake_mineracao(ids=None, token=None):
        chamadas.append(ids)
        feita = True

    monkeypatch.setattr(app_mod, "repositorios_pendentes", fake_repositorios_pendentes)
    monkeypatch.setattr(app_mod, "tarefa_mineracao", fake_mineracao)
    app_mod.iniciar_autocoleta()

    assert feita
    assert chamadas == [[7]]


def test_autocoleta_sem_pendentes(monkeypatch):
    """Quando não há repositórios pendentes, status fica 'concluido'."""
    def fake_repositorios_pendentes():
        return []

    monkeypatch.setattr(app_mod, "repositorios_pendentes", fake_repositorios_pendentes)
    app_mod.iniciar_autocoleta()

    snap = app_mod.status.snapshot()
    assert snap["estado"] == "concluido"
    assert "Nenhum repositório pendente" in snap["mensagem"]


def test_autocoleta_erro_schema(monkeypatch):
    """Se init_schema falhar, status fica 'erro'."""
    def boom():
        raise RuntimeError("x")

    monkeypatch.setattr(app_mod, "init_schema", boom)
    app_mod.iniciar_autocoleta()

    snap = app_mod.status.snapshot()
    assert snap["estado"] == "erro"
    assert "schema" in snap["mensagem"].lower()