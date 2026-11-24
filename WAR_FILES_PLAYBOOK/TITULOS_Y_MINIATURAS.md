# WAR FILES — Guía de títulos y miniaturas

Fuentes: transcripciones de *"How I Actually Make Viral Thumbnails"* (Isaac) y *"Give Me 8 Minutes, I'll Make Your Titles 81% Better"* (Aprilynne Alter), adaptadas al canal WAR FILES (documentales históricos/militares, tono serio y premium).
**Aplicar esta guía en TODOS los videos futuros del canal.**

---

## 1. Principio base
- Si no hacen clic, no ven. Título y miniatura son **un solo sistema**: el título abre una pregunta y la miniatura la amplifica. **Nunca repetir el mismo texto en los dos.**
- El viaje debe continuar miniatura → título → primeros 30 s del video (el gancho del video debe cumplir la promesa de la miniatura).

## 2. Miniaturas

### 2.1 Composición: regla de tercios
- Dibujar mentalmente 2 líneas verticales y 2 horizontales (tercios). El sujeto principal va sobre una línea vertical; su cara/cabeza o el objeto clave, cerca de una intersección.
- El texto ocupa otro tercio (normalmente el lado opuesto al sujeto, tercio superior).
- Un solo punto focal claro. Si hay que explicar qué mirar, sobra algo.

### 2.2 Paleta fija del canal (+ un color de acento que cambia)
| Rol | Color | Uso |
|---|---|---|
| Principal (marca) | Dorado apagado `#C9A54C` | detalles, fechas, cabeceras |
| Negro | `#0A0B0E` | fondos, sombras |
| Blanco roto | `#F2EFE8` | texto principal |
| Intermedio | Gris acero `#76808A` | texturas, metal, mapas |
| **Acento (variable por video)** | rojo `#E8342A`, azul hielo, verde, etc. | UNA palabra o elemento clave |

- Cambiar solo el color de acento entre videos mantiene la marca reconocible sin que todo parezca igual.

### 2.3 Tipografía
- Una sola fuente de titulares, gruesa y no sobreexplotada: **Bebas Neue** (titulares) + **Oswald** (cabeceras pequeñas). Siempre las mismas.
- Máximo 3–4 palabras grandes. Debe leerse en un móvil a tamaño real (~360 px de ancho).

### 2.4 Tipos de miniatura (combinar 2–3)
1. **Emoción objetivo / impacto**: provocar sorpresa o inquietud al hacer scroll (p. ej., "HE WAS ALREADY DEAD").
2. **Números grandes**: cifras impactantes ($100,000,000; 38 DÍAS).
3. **Simple**: un solo objeto o escena + una frase/pregunta.
4. **Cara conocida** (*social hacking*): solo si el video trata realmente de esa persona (si no, es clickbait).
5. **Cabecera**: texto pequeño arriba que da contexto ("1943 · TOP SECRET").
6. **Comparación**: antes/después, versión A vs. versión B, falso vs. real.
7. **Ocultar / difuminar** el elemento clave para obligar a hacer clic (identidad tachada, foto borrosa).
8. **Objeto extraño o inquietante**.
9. **Marca**: elementos propios reconocibles (paleta, tipografía, sello dorado).
- Mantener una combinación ~5 videos para que la audiencia reconozca el estilo; luego evolucionar (no repetirla 100 veces).

### 2.5 Inspiración
- **No copiar** la miniatura cliché del nicho (si 10 canales de historia usan la misma fórmula, la nuestra se pierde).
- Buscar ideas en canales de **otros nichos** y adaptarlas, manteniendo paleta, fuentes y estilo propios.

### 2.6 Texto en la miniatura
- Opciones: número grande · afirmación audaz contraria a lo esperado · frase corta que represente el video · o ningún texto.
- Complementa al título, no lo repite.
- Precisión histórica obligatoria: nada que el video no sostenga.

### 2.7 Acabado (efectos)
- Oscurecer suavemente detrás del texto y del sujeto (pincel suave, ~5 % de flujo) para separar capas.
- Brillo exterior / resplandor sutil en el texto clave; luz de borde (*rim light*) en el sujeto.
- Ajustar tono/saturación del fondo para que el acento destaque; difuminar fondos que distraen.
- Reflejos de luz coherentes con la fuente de luz de la escena.
- Etalonaje final de contraste/color.

### 2.8 Prueba antes de publicar
- Ver la miniatura **con su título** en una simulación de la página de inicio de YouTube (escritorio y móvil), rodeada de otras miniaturas (como hace thumbsup.tv). Si no destaca o no se lee, se rehace.
- En este proyecto: `WAR_FILES_PLAYBOOK/homepage_test.py` genera esa simulación.

### 2.9 Reglas propias de WAR FILES
- Nunca imágenes gráficas de muertos ni violencia explícita.
- Nunca presentar una ilustración como foto de archivo real.
- No usar la cara de una persona real con una afirmación que no le corresponde (p. ej., la foto del carné de "Major Martin" es de Ronnie Reed, que estaba vivo).
- Evitar símbolos nazis prominentes (riesgo de monetización); referencias sutiles (mapa, colores).

## 3. Títulos

### 3.1 Abrir un bucle de curiosidad
- El título debe hacer que el espectador se pregunte algo (¿cómo?, ¿por qué?, ¿qué pasó?). Si no hay pregunta, no hay clic.
- Contradicciones y paradojas funcionan muy bien en historia: *un muerto que engaña*, *un plan imposible que funciona*.

### 3.2 Modelar formatos probados
- Buscar *outliers* (videos que superan mucho la media de su canal) y extraer su **estructura**, no sus palabras.
- Formatos útiles para historia:
  - "The [persona/objeto inesperado] Who/That [logró algo imposible]"
  - "How [X] [verbo] [enemigo poderoso]"
  - "[Hecho imposible]. [Giro]." (dos frases cortas)
  - "The [adjetivo] [cosa] That [consecuencia enorme]"
  - "Why [grupo] [hizo algo extraño]"
  - "They [hicieron X]. Then [giro]."
  - "The True Story of [nombre conocido]" (si el tema ya es famoso)

### 3.3 Palabras poderosas
- Emocionales: dead, forgotten, haunting, strangest, desperate.
- Autoridad: true story, declassified, real, official, untold.
- Urgencia/riesgo: before, one mistake, fatal, last.
- Exclusividad: secret, hidden, never, unknown.
- Nicho historia militar (WWII): Hitler, Nazis, secret mission, spy, deception, invasion, fooled, impossible, never existed.

### 3.4 Brevedad y orden
- Ideal **≤ 55 caracteres**. Si es más largo, lo importante va **delante** (YouTube corta el final con "…").
- El mensaje central debe entenderse leyendo solo la primera mitad.

### 3.5 Medir y cambiar
- Revisar **CTR e impresiones** en las primeras 24 h. Si ambos están por debajo de la media del canal → cambiar primero el **título** (es más fácil que la miniatura).
- Si están en la media, esperar a la ventana en la que los videos del canal empiezan a despegar (ver la banda gris "típico" en YouTube Studio y dónde cambia la pendiente).
- Preparar siempre 2–3 títulos de reserva por video.

## 4. Checklist por video
- [ ] Título ≤ 55 caracteres, palabras clave delante, abre una pregunta.
- [ ] Miniatura: regla de tercios, 1 foco, ≤ 4 palabras, paleta del canal + 1 acento.
- [ ] Título y miniatura se complementan, no se repiten.
- [ ] 3 variantes de miniatura de **tipos distintos**; elegir por claridad, curiosidad, jerarquía y lectura en móvil.
- [ ] Probada en simulación de página de inicio (escritorio + móvil).
- [ ] Todo es históricamente cierto y está respaldado por el video.
- [ ] 2–3 títulos de reserva + plan de cambio según CTR.

## 5. Herramientas del proyecto
- `WAR_FILES_PLAYBOOK/homepage_test.py OUT.png "Título" thumb1.png thumb2.png ...` → simulación de inicio (escritorio + móvil) con miniaturas de relleno típicas del nicho.
- YouTube Studio permite **"Test & Compare"** (hasta 3 miniaturas): subir siempre las 3 variantes y dejar que YouTube elija.
- Ejemplo aplicado: `WAR_FILES_OPERATION_MINCEMEAT/project/src/thumbs_v2.py` (3 tipos distintos sobre la regla de tercios).

## 6. Lecciones aprendidas por video
- **Operation Mincemeat (2026-11)**: "HE WAS ALREADY DEAD" repetía la idea del título ("The Dead Man…") → se eligió "HE NEVER EXISTED" (nueva paradoja, mejor lectura en móvil). Texto rojo sobre cielo naranja pierde contraste: oscurecer detrás del texto.
- **Regla técnica**: dejar libre la **esquina inferior derecha** (~15 % ancho × 15 % alto): ahí YouTube pone la duración del video y tapa el texto. Detectado con `homepage_test.py` en Operation Mincemeat.
- Fotos aportadas por el dueño del canal (p. ej. Hitler gritando): recortar símbolos nazis (brazalete) y confirmar la licencia/origen de la foto antes de publicar.
