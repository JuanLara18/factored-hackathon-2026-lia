"""`python -m latam_ia.registro [--check]` regenera (o verifica) agentes/gateway.generado.yaml."""

import sys

from latam_ia.registro import a_yaml, cargar_registro, generar_config_gateway
from latam_ia.registro.cargador import RAIZ_IA

SALIDA = RAIZ_IA / "agentes" / "gateway.generado.yaml"


def main(argv: list[str]) -> int:
    texto = a_yaml(generar_config_gateway(cargar_registro()))
    if "--check" in argv:
        if not SALIDA.exists() or SALIDA.read_text(encoding="utf-8") != texto:
            print("gateway.generado.yaml desactualizado")
            return 1
        return 0
    SALIDA.write_text(texto, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
