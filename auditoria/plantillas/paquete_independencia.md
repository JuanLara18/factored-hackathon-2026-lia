# Paquete de independencia

Plantilla de AUD-4.2 (R-AUD-04). Cada invocación de Auditoría que emite un informe deja una carpeta
`auditoria/sesiones/<fecha>_<objeto>/` con este archivo llenado como `paquete.yaml` y con el informe
sellado. Sin el paquete completo, el informe no cuenta.

```yaml
sesion: AAAA-MM-DD_objeto            # igual al nombre de la carpeta
objeto: que se audita                # compuerta, definición, corrida, fuente
invocacion:
  agente: auditoria                  # .claude/agents/auditoria.md
  contexto: frio                     # frio: sin conversación de construcción; si no, explicar
  modelo: identificador del modelo usado
definicion_del_agente:
  ruta: .claude/agents/auditoria.md
  sha256: huella del archivo          # python -m latam_gobierno.sello <ruta>
entradas:                            # solo artefactos, nunca conversaciones
  - ruta: ruta/relativa/del/artefacto
    sha256: huella
herramientas_usadas: [Read, Grep, Glob]
informe:
  ruta: auditoria/sesiones/AAAA-MM-DD_objeto/informe.md
  sha256_hallazgos: huella del bloque sellado   # sello --bloque <informe>
  commit: hash del commit empujado antes de que la Presidencia lo lea
  rama: rama donde se empujó
segunda_revision_fria:               # R-AUD-05
  requerida: si o no
  informe: ruta o null
declaraciones:
  sin_acceso_a_credenciales: true
  sin_acceso_al_diccionario_del_dataset: true
  no_construyo_lo_auditado: true
```

## Lista de comprobación antes de sellar

- El agente arrancó sin contexto de construcción y recibió solo artefactos.
- Cada entrada tiene su huella y las huellas se recalculan sin diferencias.
- La definición del agente tiene huella y coincide con la del commit auditado.
- Las herramientas usadas son las de solo lectura más la escritura en `auditoria/`.
- Ningún archivo de credenciales ni el diccionario del dataset se leyó.
