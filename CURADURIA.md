# Cómo se arma cada edición del Clipping Renovador

Se publica tres veces por día: 6, 14 y 22 h (hora argentina). El rastrillo (GitHub Actions, cada hora) junta el material; la curaduría la hace Claude y la publica.

## Material disponible

- `data/crudo.json` — notas de Google Noticias (últimos 7 días). Campos: `id`, `titulo`, `medio`, `fecha`, `url`, `url_original` (link directo, si se pudo resolver), `busquedas` (qué búsqueda la trajo).
- `data/videos.json` — videos de YouTube subidos en el día. Campos: `id`, `titulo`, `canal`, `publicado`, `busqueda`. Trae falsos positivos (otro Giuliano, fútbol, inmobiliarias): descartarlos.
- `data/tuits.json` — tuits que los medios citaron en sus notas. Campos: `id`, `usuario`, `citado_en`.
- `data/edicion.json` — la edición anterior (para no repetir y dar continuidad).
- `data/tuits_cuentas.json` — publicaciones de las propias cuentas de los dirigentes (lista en `data/cuentas_x.txt`), leídas antes de cada edición. Campos: `url`, `autor`, `fecha`, `texto`. Es la fuente principal para `redes`.
- `data/tuits_extra.txt` — links de tuits que el equipo quiere sumar (uno por línea). Si hay alguno nuevo, agregarlo en `redes` con `"url"` en lugar de `tuit_id`.

## Dirigentes a seguir con prioridad

Además de Massa y los dirigentes que aparecen en el material, seguir a **Felipe Romero**, secretario de Juventud de Jóvenes FR CABA (también figura como "Feli Romero"). Cuando aparezca en notas, videos o tuits, incluirlo de forma natural en la sección que corresponda, como a cualquier otro dirigente: sin secciones ni etiquetas especiales. En redes (su cuenta es @felipemromeroo), sumar solo sus publicaciones más institucionales o vinculadas a la política nacional que hayan tenido buena repercusión; es un dirigente joven y no todo su perfil es político, así que nada de chistes, temas personales ni discusiones menores. Cuidado con homónimos: confirmar que se trata de él por el contexto (FR, juventud, CABA).

## Pasos

1. Tomar las notas de las **últimas 24 horas** (no solo las publicadas desde la edición anterior): cada edición tiene que poder leerse sola, como un diario completo del día. Lo nuevo desde la edición anterior va primero y actualiza los resúmenes; los temas importantes que siguen vigentes se mantienen. Sumar notas más viejas solo si el tema sigue vivo.
   - **Piso de contenido:** una edición nunca puede quedar más flaca que la anterior por falta de material nuevo. Mínimo 6 temas, 6 tuits y todas las entrevistas válidas de las últimas 48 h (si existen). Si a la madrugada hay poco nuevo, mantener los temas, tuits y entrevistas de la edición anterior que sigan vigentes, actualizando lo que haya cambiado.
   - Antes de guardar, comparar con `data/edicion.json` (la edición anterior): si la nueva tiene menos temas, tuits o entrevistas, revisar y completar.
2. Descartar lo que no es sobre Massa, el Frente Renovador o sus dirigentes: notas que los nombran de pasada, homónimos, notas de otros países, necrológicas, portadas genéricas.
3. Agrupar por tema. Si hay muchas notas de lo mismo, elegir 2 o 3 `principales`: el medio más reconocido o la nota con más información propia. El resto va en `otras` (solo se muestra el nombre del medio).
4. Ordenar los temas de mayor a menor relevancia para la dirigencia. Entre 5 y 10 temas. Incluir también la cobertura crítica (tono `negativo`): el equipo necesita verla.
5. Escribir para cada tema: `titulo` (propio, claro, sin clickbait), `resumen` (2 o 3 oraciones con palabras propias, solo lo que dicen los títulos y bajadas; no inventar datos ni citas), `tono` (`positivo`, `negativo`, `neutro` o `mixto`, desde el punto de vista del FR) y `dirigentes` (nombres completos de dirigentes del FR que aparecen).
6. `claves`: 3 o 4 puntos con lo más importante de la edición. Las leen dirigentes: registro formal y sobrio, tercera persona, sin coloquialismos, adjetivos ni expresiones como "cruzó", "chicaneó" o "le pegó". Cada punto, una o dos oraciones cortas. Nombrar cargos cuando corresponda (el gobernador, el ministro de Economía).
7. `redes`: entre 6 y 10 tuits. Primero las publicaciones políticamente relevantes de las cuentas de `data/tuits_cuentas.json` de las últimas 24 h (siempre incluir los de Sergio Massa que sean políticos), con `"url"` y `"autor": "@usuario"`. Después, los tuits citados por medios (`tuit_id`) y los de `data/tuits_extra.txt` (`url`). Solo publicaciones serias: nada de saludos de cumpleaños, efemérides menores ni temas personales. `nota` opcional de una línea.
8. `entrevistas`: solo entrevistas reales, en las que un dirigente del FR (o un referente hablando del FR) responde preguntas en un programa, radio, canal o streaming. No van: informes o notas de un medio sobre un hecho, paneles de análisis sin entrevistado, clips, recortes ni shorts. Duración mínima: 5 minutos (el armador descarta las más cortas). Mejor tres entrevistas buenas que ocho de relleno (`video_id`).
9. `hora`: "06", "14" o "22" según la edición.
10. **Encuestas** (`data/encuestas.json`): si en el material hay una encuesta nueva que mida a Massa, al FR o a sus dirigentes, agregarla. Para los números sí hay que abrir la nota (es la excepción a la regla de austeridad) y cargar solo cifras que figuren textualmente. Formato de cada entrada: `{"fecha": "AAAA-MM-DD", "consultora": "...", "alcance": "Nacional" o "Provincia de Buenos Aires", "titulo": "...", "datos": [{"etiqueta": "Imagen positiva de Sergio Massa", "valor": 25.9, "unidad": "%"}], "fuente": {"medio": "...", "url": "...", "dominio": "..."}}`. No duplicar encuestas ya cargadas.
11. **Agenda** (`data/agenda.json`): SOLO actividades del Frente Renovador y sus dirigentes. Sí: reuniones o congresos del FR nacional o provinciales, actos del FR, visitas de dirigentes del FR a provincias o municipios, entrevistas programadas de dirigentes del FR, sesiones donde un legislador del FR tenga un rol propio. No: actividades de otros partidos o del PJ (congresos, consejos, plenarios), aunque se hable de ellas en las notas, salvo que un dirigente del FR participe como orador o protagonista. Agregar actividades futuras anunciadas en el material con `fecha`, `hora` (si se sabe), `titulo`, `detalle`, `lugar`, `dirigentes` y `fuente`. Borrar las que ya pasaron hace más de un día.
12. Escribir `data/curaduria.json` y correr `python3 scripts/armar_edicion.py`. Si avisa IDs no encontrados, corregirlos.
13. Guardar: `git add data semanal.html && git commit -m "Edición <fecha> <hora> h" && git pull --rebase -X theirs && git push`.

- Descartar siempre homónimos (personas con el mismo nombre que no son nuestros dirigentes) y notas de medios del exterior que no hablen de la política argentina.

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

- No usar "massista", "massismo" ni equivalentes para describir a dirigentes propios: es un clipping del FR y es redundante. Nombrar a cada uno por su nombre y cargo. (Se puede usar solo si aparece en una cita textual de un medio.)

- No copiar párrafos de las notas: resúmenes propios y cortos.
- No tocar `index.html`, los scripts ni el workflow.
- Ser austero: leer los JSON con scripts cortos, sin abrir cada nota. Usar búsqueda web solo si un tema central no se entiende con los títulos.

## Clipping Semanal (sábados)

1. La semana son SIEMPRE los 7 días completos hacia atrás: de domingo a sábado (`desde` = sábado − 6 días, `hasta` = el sábado de la corrida). Nunca armar el semanal solo con lo del último día.
   - Leer todas las ediciones de esos 7 días en `data/ediciones/` y todo lo que haya en `data/crudo.json`, `data/videos.json` y `data/tuits.json` (guardan 7 días).
   - Si faltan días (por ejemplo, la primera semana), completar con búsquedas web de esos días (Google Noticias, YouTube) antes de elegir. El resumen tiene que cubrir la semana entera.
2. Escribir `data/semanal/curaduria.json` con el mismo formato que la diaria más `"desde": "AAAA-MM-DD"` y `"hasta": "AAAA-MM-DD"`.
   - `claves`: 4 o 5 puntos que resuman la semana, en el mismo registro formal y sobrio.
   - `temas`: los 6 a 10 temas más importantes de la semana, cada uno con resumen de la semana completa (no del último día) y sus 2 o 3 mejores notas.
   - `entrevistas`: las mejores entrevistas de la semana (máximo 8). `redes`: los tuits más relevantes (máximo 8).
3. Correr `python3 scripts/armar_edicion.py --semanal` y guardar con git como la diaria.
