"""Ponto de entrada simples para validar que o ambiente inicial está funcionando."""

from __future__ import annotations

from rich.console import Console

console = Console()


def main() -> None:
    """Executa uma mensagem inicial para confirmar que o projeto está configurado.

    Neste momento o projeto ainda não tem a lógica principal do coach.
    A função existe apenas para validar se o Python, o ambiente virtual
    e as dependências básicas foram instalados corretamente.
    """

    console.print("[bold green]English Voice Coach iniciado com sucesso![/bold green]")
    console.print("Ambiente configurado. Próximo passo: captura de áudio.")


if __name__ == "__main__":
    main()
