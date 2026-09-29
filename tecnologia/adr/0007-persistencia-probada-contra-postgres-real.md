# ADR 0007: Persistencia probada contra Postgres real

- **Estado:** firme
- **Decisión de origen:** D-23 (DP-TEC-06, enmienda de D-20) (`presidencia/decisiones.md`)
- **Principio que la guía:** P13

## Contexto

Un SQLite en pruebas oculta diferencias con Postgres (unicidad parcial, jsonb, concurrencia) y produce deriva entre local y nube (H-AUD-07).

## Opciones consideradas

SQLite en todas las pruebas de persistencia.

## Decisión

Las pruebas de persistencia corren contra Postgres real en contenedor; SQLite solo en pruebas unitarias sin SQL.

## Consecuencias

Pruebas más fieles a producción. Exigen Docker en CI; localmente, las pruebas de integración se omiten si Docker no está disponible y las unitarias siguen cubriendo la lógica pura.
