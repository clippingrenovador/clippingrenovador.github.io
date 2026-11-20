# Cómo se arma cada edición del Clipping Renovador

Se publica tres veces por día: 6, 14 y 22 h (hora argentina). El rastrillo (GitHub Actions, cada hora) junta el material; la curaduría la hace Claude y la publica.

## Material disponible

- `data/crudo.json` — notas de Google Noticias (últimos 7 días). Campos: `id`, `titulo`, `medio`, `fecha`, `url`, `url_original` (link directo, si se pudo resolver), `busquedas` (qué búsqueda la trajo).
- `data/videos.json` — videos de YouTube subidos en el día. Campos: `id`, `titulo`, `canal`, `publicado`, `busqueda`. Trae falsos positivos (otro Giuliano, fútbol, inmobiliarias): descartarlos.
- `data/tuits.json` — tuits que los medios citaron en sus notas. Campos: `id`, `usuario`, `citado_en`.
- `data/edicion.json` — la edición anterior (para no repetir y dar continuidad).

## Pasos

1. Tomar las notas publicadas desde la edición anterior (mirar `generado` en `data/edicion.json`; si falta, últimas 12 h). Sumar notas más viejas solo si el tema sigue vivo.
2. Descartar lo que no es sobre Massa, el Frente Renovador o sus dirigentes: notas que los nombran de pasada, homónimos, notas de otros países, necrológicas, portadas genéricas.
3. Agrupar por tema. Si hay muchas notas de lo mismo, elegir 2 o 3 `principales`: el medio más reconocido o la nota con más información propia. El resto va en `otras` (solo se muestra el nombre del medio).
4. Ordenar los temas de mayor a menor relevancia para la dirigencia. Entre 5 y 10 temas. Incluir también la cobertura crítica (tono `negativo`): el equipo necesita verla.
5. Escribir para cada tema: `titulo` (propio, claro, sin clickbait), `resumen` (2 o 3 oraciones con palabras propias, solo lo que dicen los títulos y bajadas; no inventar datos ni citas), `tono` (`positivo`, `negativo`, `neutro` o `mixto`, desde el punto de vista del FR) y `dirigentes` (nombres completos de dirigentes del FR que aparecen).
6. `claves`: 3 o 4 oraciones con lo más importante de la edición, para leer en 30 segundos.
7. `redes`: hasta 6 tuits, priorizando cuentas de dirigentes del FR (`tuit_id` del archivo). `nota` opcional de una línea.
8. `entrevistas`: hasta 8 videos con dirigentes del FR o análisis centrales sobre Massa y el FR (`video_id`).
9. `hora`: "06", "14" o "22" según la edición.
10. Escribir `data/curaduria.json` y correr `python3 scripts/armar_edicion.py`. Si avisa IDs no encontrados, corregirlos.
11. Guardar: `git add data && git commit -m "Edición <fecha> <hora> h" && git pull --rebase -X theirs && git push`.

## Formato de data/curaduria.json

```json
{
  "hora": "14",
  "claves": ["...", "..."],
  "temas": [
    {"titulo": "...", "resumen": "...", "tono": "positivo", "dirigentes": ["Sergio Massa"],
     "principales": ["<id nota>", "<id nota>"], "otras": ["<id nota>"]}
  ],
  "redes": [{"tuit_id": "<id>", "nota": "..."}],
  "entrevistas": [{"video_id": "<id>"}]
}
```

## Reglas

- No copiar párrafos de las notas: resúmenes propios y cortos.
- No tocar `index.html`, los scripts ni el workflow.
- Ser austero: leer los JSON con scripts cortos, sin abrir cada nota. Usar búsqueda web solo si un tema central no se entiende con los títulos.
