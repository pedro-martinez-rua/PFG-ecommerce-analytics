BENCHMARK_CASES = [
    {
        "id": "case_01_growth_healthy_low_retention",
        "name": "Crecimiento sano con recompra baja",
        "period": "last_90",
        "kpis": {
            "total_revenue":   {"value": 48320.0,  "growth_pct": 12.4,  "availability": "real"},
            "order_count":     {"value": 312.0,    "growth_pct": 8.1,   "availability": "real"},
            "avg_order_value": {"value": 154.87,   "growth_pct": 3.9,   "availability": "real"},
            "net_revenue":     {"value": 44250.0,  "growth_pct": None,  "availability": "real"},
            "gross_margin_pct":{"value": 52.3,     "growth_pct": None,  "availability": "real"},
            "gross_margin":    {"value": 25271.0,  "growth_pct": None,  "availability": "real"},
            "total_refunds":   {"value": 1840.0,   "growth_pct": None,  "availability": "real"},
            "refund_rate":     {"value": 3.8,      "growth_pct": None,  "availability": "real"},
            "unique_customers":{"value": 198.0,    "growth_pct": None,  "availability": "real"},
            "repeat_purchase_rate": {"value": 17.2,"growth_pct": None,  "availability": "real"},
            "avg_customer_ltv":{"value": 244.04,   "growth_pct": None,  "availability": "real"},
            "new_vs_returning":{"value": {"new": 164, "returning": 34}, "availability": "real"},
            "return_rate":     {"value": 6.1,      "growth_pct": None,  "availability": "real"},
            "returned_orders": {"value": 19.0,     "growth_pct": None,  "availability": "real"},
            "avg_delivery_days":{"value": 4.2,     "growth_pct": None,  "availability": "real"},
            "delayed_orders_pct":{"value": 8.7,    "growth_pct": None,  "availability": "real"},
            "total_discounts": {"value": 2230.0,   "growth_pct": None,  "availability": "real"},
            "discount_rate":   {"value": 4.6,      "growth_pct": None,  "availability": "real"},
        },
        "coverage": {
            "has_cogs": True, "has_channels": False, "has_countries": False,
            "has_returns": True, "has_discounts": True, "has_delivery": True,
            "has_customers": True, "has_categories": False, "has_products": False,
        },
        "charts": {
            "revenue_over_time": [
                {"label": "2024-01", "value": 14200.0},
                {"label": "2024-02", "value": 16850.0},
                {"label": "2024-03", "value": 17270.0},
            ],
            "orders_over_time": [
                {"label": "2024-01", "value": 89},
                {"label": "2024-02", "value": 107},
                {"label": "2024-03", "value": 116},
            ],
        },
        "reference_explanation": """
Tu negocio ha generado 48.320 euros en revenue bruto durante los últimos 90 días,
procesando un total de 312 pedidos con un valor medio de 154,87 euros por pedido.
Esto representa un crecimiento del 12,4% en facturación respecto al periodo anterior,
impulsado también por un aumento del 8,1% en el número de pedidos y un incremento
del 3,9% en el valor medio por pedido. La tendencia es claramente positiva: el revenue
ha pasado de 14.200 euros en enero a 17.270 euros en marzo, lo que equivale a un
crecimiento del 21,6% en solo tres meses.

El margen bruto del 52,3% se sitúa en la banda media-alta del sector e-commerce,
donde el rango normal es del 40 al 60%. Esto significa que de cada 100 euros que
ingresas, 52,30 euros quedan después de cubrir el coste directo del producto.
En términos absolutos, el beneficio bruto del periodo fue de 25.271 euros,
que es el dinero real disponible para cubrir marketing, logística, operaciones
y beneficio neto. Es un resultado sólido que indica que la estructura de precios
y costes está bien calibrada.

El revenue neto, una vez descontados reembolsos y descuentos, fue de 44.250 euros.
Los descuentos aplicados totalizaron 2.230 euros, representando el 4,6% del revenue bruto,
lo que se considera saludable ya que está por debajo del umbral del 5% recomendado.
Los reembolsos sumaron 1.840 euros, con una tasa del 3,8%, también por debajo del
benchmark del 5%, lo que indica que los clientes están recibiendo lo que esperaban.

Sin embargo, hay un área que requiere atención urgente: la retención de clientes.
De los 198 clientes únicos del periodo, 164 son nuevos y solo 34 son recurrentes.
Esto da una tasa de recompra del 17,2%, por debajo del mínimo recomendable del 20%.
El LTV medio por cliente es de 244 euros, lo que representa un ratio LTV/AOV de 1,57x,
muy por debajo del benchmark saludable de 3x o más. En la práctica, esto significa
que estás invirtiendo en captar clientes que mayoritariamente solo compran una vez.
Si consiguieras que el 25% de los clientes nuevos repitiera compra en los próximos
90 días, el revenue podría aumentar entre 6.000 y 8.000 euros adicionales sin
necesidad de aumentar el presupuesto de captación.

En cuanto a la operación logística, el tiempo de entrega promedio es de 4,2 días,
dentro del rango normal de 3 a 7 días. No obstante, el 8,7% de los pedidos
se entrega con retraso, lo que afecta a 27 pedidos en el periodo.
Aunque está por debajo del umbral crítico del 10%, es un indicador que conviene
vigilar porque los retrasos impactan directamente en la satisfacción del cliente
y en la probabilidad de recompra. La tasa de devoluciones del 6,1% está ligeramente
por encima del benchmark excelente del 5%, con 19 pedidos devueltos en el periodo.

Plan de acción inmediato para las próximas dos semanas: configura un email automático
que se envíe exactamente 15 días después de cada primera compra a los 164 nuevos clientes
del periodo, incluyendo una recomendación personalizada basada en su compra anterior
y un descuento del 10% de duración limitada a 72 horas. Este tipo de campaña de
activación temprana puede convertir entre un 8 y un 15% de los nuevos clientes
en recurrentes, lo que en tu caso equivaldría a entre 13 y 24 clientes adicionales
con una segunda compra de 154 euros de media. Para reducir los retrasos logísticos,
identifica los 27 pedidos afectados y analiza si comparten proveedor, zona geográfica
o tipo de producto, ya que el problema suele estar concentrado y es más fácil de resolver
de lo que parece. En paralelo, revisa los 19 pedidos devueltos para identificar si hay
un producto concreto con alta tasa de devolución, porque mejorar la descripción o las
fotos de ese producto puede reducir las devoluciones en un 20-30% en pocas semanas.

En resumen, tienes un negocio con crecimiento sólido, márgenes saludables y una
operación bajo control. El único punto débil real es la retención: si resuelves eso,
el negocio puede crecer un 15-20% adicional sin necesidad de captar más clientes nuevos.
""",
        "fact_checks": [
            {
                "id": "margin_healthy",
                "type": "classification",
                "accepted_terms": ["52,3", "52.3", "margen", "saludable", "resultado solido", "estructura de precios", "banda"],
            },
            {
                "id": "retention_problem",
                "type": "classification",
                "accepted_terms": ["17,2", "retencion", "recompra", "por debajo del 20", "clientes recurrentes"],
            },
            {
                "id": "trend_positive",
                "type": "trend",
                "accepted_terms": ["tendencia positiva", "crecimiento", "ha pasado de 14.200", "ha aumentado"],
            },
            {
                "id": "no_channels",
                "type": "forbidden_topic",
                "topic_terms": ["meta ads", "google ads", "seo", "canal principal"],
            },
        ],
    },

    {
        "id": "case_02_revenue_drop_low_margin",
        "name": "Caída de ventas con margen bajo",
        "period": "last_90",
        "kpis": {
            "total_revenue":   {"value": 18450.0,  "growth_pct": -18.6, "availability": "real"},
            "order_count":     {"value": 164.0,    "growth_pct": -12.4, "availability": "real"},
            "avg_order_value": {"value": 112.50,   "growth_pct": -7.2,  "availability": "real"},
            "net_revenue":     {"value": 15680.0,  "growth_pct": None,  "availability": "real"},
            "gross_margin_pct":{"value": 27.4,     "growth_pct": None,  "availability": "real"},
            "gross_margin":    {"value": 5055.0,   "growth_pct": None,  "availability": "real"},
            "total_refunds":   {"value": 980.0,    "growth_pct": None,  "availability": "real"},
            "refund_rate":     {"value": 5.3,      "growth_pct": None,  "availability": "real"},
            "unique_customers":{"value": 151.0,    "growth_pct": None,  "availability": "real"},
            "repeat_purchase_rate": {"value": 12.1,"growth_pct": None,  "availability": "real"},
            "avg_customer_ltv":{"value": 146.0,    "growth_pct": None,  "availability": "real"},
            "new_vs_returning":{"value": {"new": 133, "returning": 18}, "availability": "real"},
            "return_rate":     {"value": 9.8,      "growth_pct": None,  "availability": "real"},
            "returned_orders": {"value": 16.0,     "growth_pct": None,  "availability": "real"},
            "avg_delivery_days":{"value": 5.8,     "growth_pct": None,  "availability": "real"},
            "delayed_orders_pct":{"value": 11.2,   "growth_pct": None,  "availability": "real"},
            "total_discounts": {"value": 2210.0,   "growth_pct": None,  "availability": "real"},
            "discount_rate":   {"value": 12.0,     "growth_pct": None,  "availability": "real"},
        },
        "coverage": {
            "has_cogs": True, "has_channels": False, "has_countries": False,
            "has_returns": True, "has_discounts": True, "has_delivery": True,
            "has_customers": True, "has_categories": False, "has_products": False,
        },
        "charts": {
            "revenue_over_time": [
                {"label": "2024-01", "value": 7200.0},
                {"label": "2024-02", "value": 6150.0},
                {"label": "2024-03", "value": 5100.0},
            ],
            "orders_over_time": [
                {"label": "2024-01", "value": 62},
                {"label": "2024-02", "value": 55},
                {"label": "2024-03", "value": 47},
            ],
        },
        "reference_explanation": """
Tu negocio ha generado 18.450 euros en revenue bruto durante los últimos 90 días,
procesando un total de 164 pedidos con un valor medio de 112,50 euros por pedido.
Sin embargo, la evolución del negocio es claramente negativa: la facturación cae
un 18,6% respecto al periodo anterior, el número de pedidos desciende un 12,4%
y el valor medio por pedido también retrocede un 7,2%. La tendencia temporal
confirma este deterioro: el revenue ha pasado de 7.200 euros en enero a 5.100 euros
en marzo, lo que supone una caída aproximada del 29,2% en tres meses.

El margen bruto del 27,4% está por debajo del nivel recomendable en e-commerce,
donde un negocio sano suele moverse al menos por encima del 40%. Esto significa
que de cada 100 euros que ingresas, solo 27,40 euros quedan después de cubrir
el coste directo del producto. En términos absolutos, el beneficio bruto fue
de 5.055 euros, una cifra muy ajustada para sostener marketing, operaciones
y beneficio neto. La estructura actual de precios, promociones y costes no está
bien equilibrada y eso limita mucho la capacidad del negocio para crecer con rentabilidad.

El revenue neto del periodo fue de 15.680 euros. Los descuentos aplicados sumaron
2.210 euros, equivalentes al 12% del revenue bruto, un nivel elevado que está erosionando
directamente el margen. Los reembolsos fueron de 980 euros, con una tasa del 5,3%,
ligeramente por encima del umbral saludable del 5%. No es una situación extrema,
pero sí una señal de que parte de las ventas no se consolidan con la calidad esperada.

La segunda gran debilidad del negocio está en la retención. De 151 clientes únicos,
133 son nuevos y solo 18 son recurrentes. La tasa de recompra del 12,1% está muy
por debajo del mínimo recomendable del 20%, y el LTV medio por cliente es de 146 euros,
lo que refleja una vida comercial muy corta. El ratio LTV/AOV queda muy por debajo
del benchmark saludable de 3x, así que estás invirtiendo en captar clientes que
casi nunca vuelven a comprar. En la práctica, eso hace que cada euro invertido en
captación sea más difícil de rentabilizar.

En cuanto a la operación, el tiempo medio de entrega de 5,8 días está dentro de un rango
todavía aceptable, pero el 11,2% de los pedidos llega con retraso, superando el nivel
recomendable del 10%. La tasa de devoluciones del 9,8% tampoco es crítica, pero sí lo
bastante alta como para añadir fricción y coste en un momento en el que el negocio
ya tiene un margen débil.

Plan de acción inmediato para las próximas dos semanas: revisa los productos o familias
de producto con menor margen y sube precios selectivamente entre un 5% y un 8% allí
donde la elasticidad lo permita. En paralelo, reduce descuentos generales y sustituye
parte de las promociones masivas por campañas más segmentadas para clientes con mayor
probabilidad de conversión. Activa una campaña de reactivación sobre clientes que ya
compraron pero no han repetido, con una oferta limitada y personalizada. Además,
analiza la caída mensual para detectar si se concentra en un producto, una categoría
o una franja temporal concreta, porque ahí estará probablemente la fuente principal del problema.

En resumen, el negocio no solo vende menos, sino que además gana poco por cada venta.
La prioridad absoluta es corregir margen y recuperar demanda, porque sin esas dos piezas
no habrá una base sana para crecer.
""",
        "fact_checks": [
            {
                "id": "negative_trend",
                "type": "trend",
                "accepted_terms": ["cae", "cai", "evolucion negativa", "retrocede", "caida", "tendencia temporal", "descend", "negativ", "disminuy"],
            },
            {
                "id": "low_margin",
                "type": "classification",
                "accepted_terms": ["27,4", "margen bruto", "por debajo", "rentabilidad", "muy ajustada"],
            },
            {
                "id": "high_discount",
                "type": "classification",
                "accepted_terms": ["12%", "descuentos", "erosionando", "nivel elevado"],
            },
            {
                "id": "no_channels",
                "type": "forbidden_topic",
                "topic_terms": ["meta ads", "google ads", "seo", "email como canal"],
            },
        ],
    },

    {
        "id": "case_03_high_returns_and_delays",
        "name": "Devoluciones y retrasos elevados",
        "period": "last_90",
        "kpis": {
            "total_revenue":   {"value": 29880.0,  "growth_pct": 4.8,   "availability": "real"},
            "order_count":     {"value": 241.0,    "growth_pct": 2.5,   "availability": "real"},
            "avg_order_value": {"value": 123.98,   "growth_pct": 2.2,   "availability": "real"},
            "net_revenue":     {"value": 25100.0,  "growth_pct": None,  "availability": "real"},
            "gross_margin_pct":{"value": 44.1,     "growth_pct": None,  "availability": "real"},
            "gross_margin":    {"value": 13177.0,  "growth_pct": None,  "availability": "real"},
            "total_refunds":   {"value": 2480.0,   "growth_pct": None,  "availability": "real"},
            "refund_rate":     {"value": 8.3,      "growth_pct": None,  "availability": "real"},
            "unique_customers":{"value": 193.0,    "growth_pct": None,  "availability": "real"},
            "repeat_purchase_rate": {"value": 21.4,"growth_pct": None,  "availability": "real"},
            "avg_customer_ltv":{"value": 286.0,    "growth_pct": None,  "availability": "real"},
            "new_vs_returning":{"value": {"new": 142, "returning": 51}, "availability": "real"},
            "return_rate":     {"value": 14.8,     "growth_pct": None,  "availability": "real"},
            "returned_orders": {"value": 36.0,     "growth_pct": None,  "availability": "real"},
            "avg_delivery_days":{"value": 7.9,     "growth_pct": None,  "availability": "real"},
            "delayed_orders_pct":{"value": 24.2,   "growth_pct": None,  "availability": "real"},
            "total_discounts": {"value": 1190.0,   "growth_pct": None,  "availability": "real"},
            "discount_rate":   {"value": 4.0,      "growth_pct": None,  "availability": "real"},
        },
        "coverage": {
            "has_cogs": True, "has_channels": False, "has_countries": False,
            "has_returns": True, "has_discounts": True, "has_delivery": True,
            "has_customers": True, "has_categories": False, "has_products": False,
        },
        "charts": {
            "revenue_over_time": [
                {"label": "2024-01", "value": 9800.0},
                {"label": "2024-02", "value": 10020.0},
                {"label": "2024-03", "value": 10060.0},
            ],
            "orders_over_time": [
                {"label": "2024-01", "value": 78},
                {"label": "2024-02", "value": 80},
                {"label": "2024-03", "value": 83},
            ],
        },
        "reference_explanation": """
Tu negocio ha generado 29.880 euros en revenue bruto durante los últimos 90 días,
procesando 241 pedidos con un valor medio de 123,98 euros por pedido. La evolución
general es positiva, aunque moderada: la facturación crece un 4,8%, los pedidos
aumentan un 2,5% y el AOV sube un 2,2%. La tendencia temporal muestra estabilidad
con ligera mejora, al pasar de 9.800 euros en enero a 10.060 euros en marzo.
A primera vista, la demanda no parece ser el principal problema del negocio.

El margen bruto del 44,1% entra dentro del rango normal del sector e-commerce,
por lo que la rentabilidad base es aceptable. En términos absolutos, el beneficio
bruto del periodo fue de 13.177 euros, suficiente para sostener la operación si el resto
de variables se mantiene bajo control. El revenue neto, tras descuentos y reembolsos,
fue de 25.100 euros. Los descuentos representan solo un 4% del revenue bruto,
por debajo del umbral del 5%, así que no parece que estés sacrificando demasiado margen
a través de promociones.

Donde sí aparece el verdadero problema es en la fase posterior a la compra.
Los reembolsos ascienden a 2.480 euros y la tasa de reembolso es del 8,3%, claramente
por encima del nivel saludable. La tasa de devoluciones alcanza el 14,8%, muy cerca
de una zona preocupante en e-commerce, con 36 pedidos devueltos en el periodo.
Además, el tiempo medio de entrega es de 7,9 días, cerca del límite superior de lo normal,
y el 24,2% de los pedidos se entrega con retraso. Eso significa que aproximadamente
1 de cada 4 pedidos llega tarde, una cifra demasiado alta para una operación que quiera
proteger satisfacción, repetición y reputación.

En la parte de clientes, la situación es bastante mejor. La tasa de recompra del 21,4%
ya está en una banda normal y el LTV medio por cliente se sitúa en 286 euros,
lo que indica una base algo más sana que en escenarios de retención débil. Precisamente
por eso el mayor riesgo aquí no es comercial, sino operativo: si logística y devoluciones
siguen deteriorándose, terminarán afectando también a la recompra y al margen.

Plan de acción inmediato para las próximas dos semanas: identifica los 36 pedidos
devueltos y clasifícalos por motivo, producto y proveedor para localizar patrones
repetidos. En paralelo, analiza el 24,2% de entregas retrasadas y comprueba si se
concentran en una zona geográfica, un operador o un tipo de producto. Si el problema
está agrupado, podrás corregirlo mucho más rápido. También conviene revisar las fichas
de producto con más devoluciones, porque mejorar descripción, imágenes o expectativas
puede reducir devoluciones entre un 15% y un 30% sin tocar captación.

En resumen, no estás ante un problema serio de ventas, sino ante un problema de ejecución
postcompra. Si corriges logística y devoluciones, protegerás margen, experiencia y repetición.
""",
        "fact_checks": [
            {
                "id": "returns_problem",
                "type": "classification",
                "accepted_terms": ["14,8", "devoluciones", "36 pedidos", "zona preocupante", "verdadero problema"],
            },
            {
                "id": "delays_problem",
                "type": "classification",
                "accepted_terms": ["24,2", "24.2", "retraso", "retrasad", "entrega", "1 de cada 4", "llega tarde"],
            },
            {
                "id": "not_demand_problem",
                "type": "classification",
                "accepted_terms": ["demanda no parece", "no es un problema serio de ventas", "problema operativo", "postcompra", "no es de ventas", "no hay problema de ventas", "ventas crecen", "ventas se mantienen", "demanda estable", "problema no esta en las ventas", "problema no es de demanda", "crecimiento moderado"],
            },
            {
                "id": "no_channels",
                "type": "forbidden_topic",
                "topic_terms": ["meta ads", "google ads", "seo", "canal principal"],
            },
        ],
    },

    {
        "id": "case_04_missing_data_respect",
        "name": "Respeto a datos faltantes",
        "period": "last_90",
        "kpis": {
            "total_revenue":   {"value": 22100.0,  "growth_pct": 6.4,   "availability": "real"},
            "order_count":     {"value": 174.0,    "growth_pct": 4.0,   "availability": "real"},
            "avg_order_value": {"value": 126.95,   "growth_pct": 2.3,   "availability": "real"},
            "net_revenue":     {"value": 20550.0,  "growth_pct": None,  "availability": "real"},
            "gross_margin_pct":{"value": None,     "growth_pct": None,  "availability": "missing"},
            "gross_margin":    {"value": None,     "growth_pct": None,  "availability": "missing"},
            "total_refunds":   {"value": None,     "growth_pct": None,  "availability": "missing"},
            "refund_rate":     {"value": None,     "growth_pct": None,  "availability": "missing"},
            "unique_customers":{"value": 149.0,    "growth_pct": None,  "availability": "real"},
            "repeat_purchase_rate": {"value": 22.8,"growth_pct": None,  "availability": "real"},
            "avg_customer_ltv":{"value": 311.0,    "growth_pct": None,  "availability": "real"},
            "new_vs_returning":{"value": {"new": 109, "returning": 40}, "availability": "real"},
            "return_rate":     {"value": None,     "growth_pct": None,  "availability": "missing"},
            "returned_orders": {"value": None,     "growth_pct": None,  "availability": "missing"},
            "avg_delivery_days":{"value": None,    "growth_pct": None,  "availability": "missing"},
            "delayed_orders_pct":{"value": None,   "growth_pct": None,  "availability": "missing"},
            "total_discounts": {"value": 660.0,    "growth_pct": None,  "availability": "real"},
            "discount_rate":   {"value": 3.0,      "growth_pct": None,  "availability": "real"},
        },
        "coverage": {
            "has_cogs": False, "has_channels": False, "has_countries": False,
            "has_returns": False, "has_discounts": True, "has_delivery": False,
            "has_customers": True, "has_categories": False, "has_products": False,
        },
        "charts": {
            "revenue_over_time": [
                {"label": "2024-01", "value": 7100.0},
                {"label": "2024-02", "value": 7360.0},
                {"label": "2024-03", "value": 7640.0},
            ],
            "orders_over_time": [
                {"label": "2024-01", "value": 54},
                {"label": "2024-02", "value": 58},
                {"label": "2024-03", "value": 62},
            ],
        },
        "reference_explanation": """
Tu negocio ha generado 22.100 euros en revenue bruto durante los últimos 90 días,
procesando un total de 174 pedidos con un valor medio de 126,95 euros por pedido.
La evolución del negocio es moderadamente positiva: la facturación crece un 6,4%,
los pedidos aumentan un 4% y el AOV sube un 2,3%. La tendencia temporal también
acompaña, ya que el revenue ha pasado de 7.100 euros en enero a 7.640 euros en marzo,
lo que refleja una mejora estable aunque sin aceleración fuerte.

El revenue neto del periodo fue de 20.550 euros. Los descuentos aplicados fueron
de 660 euros, equivalentes al 3% del revenue bruto, una cifra saludable y claramente
por debajo del umbral del 5% recomendado. En la parte de clientes, el negocio muestra
una señal razonable: de 149 clientes únicos, 40 son recurrentes, y la tasa de recompra
alcanza el 22,8%, ya dentro de la banda normal del sector. El LTV medio por cliente
es de 311 euros, un dato que apunta a una relación comercial más sólida que en negocios
con recompra muy débil.

Sin embargo, este caso tiene una limitación importante: faltan datos críticos para hacer
un diagnóstico completo. No dispones de margen bruto real, tampoco de información sobre
reembolsos, devoluciones ni tiempos de entrega. Eso significa que no se puede evaluar
con rigor la rentabilidad final ni la calidad de la operación postcompra. Lo correcto aquí
no es inventar conclusiones, sino reconocer que el análisis está condicionado por la falta
de cobertura en esas áreas.

En la práctica, el negocio muestra señales favorables en ventas, descuentos y recurrencia,
pero todavía no tienes suficiente información para afirmar si la rentabilidad es buena
o si la experiencia logística está bajo control. Si el margen estuviera deteriorado o las
devoluciones fueran elevadas, el diagnóstico cambiaría bastante, así que esa ausencia de datos
es relevante y no un detalle menor.

Plan de acción inmediato para las próximas dos semanas: prioriza la incorporación de costes
de producto para poder calcular margen bruto real, y añade trazabilidad de devoluciones,
reembolsos y tiempos de entrega. Sin esos datos, tus decisiones estratégicas estarán basadas
solo en una parte del negocio. Mientras completas esa cobertura, puedes seguir trabajando
acciones suaves de fidelización, porque la recompra actual ya ofrece una base razonable
sobre la que construir.

En resumen, el negocio parece evolucionar de forma correcta, pero el análisis todavía no está
cerrado porque faltan métricas críticas de rentabilidad y operación. Antes de sacar conclusiones
más ambiciosas, necesitas completar la calidad del dato.
""",
        "fact_checks": [
            {
                "id": "mentions_missing_data",
                "type": "classification",
                "accepted_terms": ["faltan datos", "no se puede evaluar", "no dispones", "limitacion importante", "no es inventar conclusiones", "datos criticos", "datos que faltan", "no hay datos", "sin datos", "informacion no disponible", "ausencia de datos"],
            },
            {
                "id": "good_discount",
                "type": "classification",
                "accepted_terms": ["3%", "descuentos", "saludable", "por debajo del 5"],
            },
            {
                "id": "normal_repeat",
                "type": "classification",
                "accepted_terms": ["22,8", "recompra", "banda normal", "40 son recurrentes"],
            },
            {
                "id": "forbidden_margin_claim",
                "type": "forbidden_topic",
                "topic_terms": ["margen saludable", "margen bruto del", "rentabilidad excelente", "beneficio bruto"],
            },
        ],
    },

    {
        "id": "case_05_estimated_margin_and_channels",
        "name": "Margen estimado y canales",
        "period": "last_90",
        "kpis": {
            "total_revenue":   {"value": 56400.0,  "growth_pct": 14.1,  "availability": "real"},
            "order_count":     {"value": 428.0,    "growth_pct": 10.2,  "availability": "real"},
            "avg_order_value": {"value": 131.78,   "growth_pct": 3.6,   "availability": "real"},
            "net_revenue":     {"value": 52190.0,  "growth_pct": None,  "availability": "real"},
            "gross_margin_pct":{"value": 48.6,     "growth_pct": None,  "availability": "estimated"},
            "gross_margin":    {"value": 27410.0,  "growth_pct": None,  "availability": "estimated"},
            "total_refunds":   {"value": 1730.0,   "growth_pct": None,  "availability": "real"},
            "refund_rate":     {"value": 3.1,      "growth_pct": None,  "availability": "real"},
            "unique_customers":{"value": 301.0,    "growth_pct": None,  "availability": "real"},
            "repeat_purchase_rate": {"value": 28.7,"growth_pct": None,  "availability": "real"},
            "avg_customer_ltv":{"value": 382.0,    "growth_pct": None,  "availability": "real"},
            "new_vs_returning":{"value": {"new": 216, "returning": 85}, "availability": "real"},
            "return_rate":     {"value": 4.4,      "growth_pct": None,  "availability": "real"},
            "returned_orders": {"value": 18.0,     "growth_pct": None,  "availability": "real"},
            "avg_delivery_days":{"value": 3.6,     "growth_pct": None,  "availability": "real"},
            "delayed_orders_pct":{"value": 6.2,    "growth_pct": None,  "availability": "real"},
            "total_discounts": {"value": 2480.0,   "growth_pct": None,  "availability": "real"},
            "discount_rate":   {"value": 4.4,      "growth_pct": None,  "availability": "real"},
        },
        "coverage": {
            "has_cogs": True, "has_channels": True, "has_countries": False,
            "has_returns": True, "has_discounts": True, "has_delivery": True,
            "has_customers": True, "has_categories": False, "has_products": False,
        },
        "charts": {
            "revenue_over_time": [
                {"label": "2024-01", "value": 17100.0},
                {"label": "2024-02", "value": 18750.0},
                {"label": "2024-03", "value": 20550.0},
            ],
            "orders_over_time": [
                {"label": "2024-01", "value": 132},
                {"label": "2024-02", "value": 141},
                {"label": "2024-03", "value": 155},
            ],
            "revenue_by_channel": [
                {"label": "Meta Ads", "value": 22100.0},
                {"label": "Email", "value": 16800.0},
                {"label": "Organic", "value": 12300.0},
                {"label": "Google Ads", "value": 5200.0},
            ],
        },
        "reference_explanation": """
Tu negocio ha generado 56.400 euros en revenue bruto durante los últimos 90 días,
procesando un total de 428 pedidos con un valor medio de 131,78 euros por pedido.
La evolución es claramente positiva: la facturación crece un 14,1%, el número de pedidos
sube un 10,2% y el AOV mejora un 3,6%. La tendencia temporal también acompaña con claridad,
ya que el revenue pasa de 17.100 euros en enero a 20.550 euros en marzo, lo que equivale
a un crecimiento aproximado del 20,2% en solo tres meses.

El margen bruto se sitúa en el 48,6%, dentro de una banda saludable para e-commerce.
Sin embargo, aquí hay una matización clave: se trata de un margen estimado y no de una
medición completa, por lo que conviene interpretarlo con prudencia. Aun así, el beneficio
bruto estimado del periodo sería de 27.410 euros, una base sólida para operar con margen
razonable. El revenue neto fue de 52.190 euros. Los descuentos representan un 4,4% del
revenue bruto, por debajo del umbral saludable del 5%, y los reembolsos se quedan en un 3,1%,
otra señal positiva de calidad comercial.

En la parte de clientes, el negocio muestra una situación mucho más sana que otros escenarios
más débiles. De 301 clientes únicos, 85 son recurrentes y la tasa de recompra alcanza el 28,7%,
dentro de una banda buena. El LTV medio por cliente se sitúa en 382 euros, lo que apunta a una
base de clientes con mayor valor a medio plazo. También la operación está bajo control:
la tasa de devoluciones es del 4,4%, el tiempo medio de entrega es de 3,6 días y solo el 6,2%
de los pedidos llega con retraso.

Además, en este caso sí tienes un dato especialmente útil: la distribución del revenue por canal.
Meta Ads lidera con 22.100 euros, seguido por Email con 16.800 euros y Organic con 12.300 euros.
Google Ads se queda muy por detrás con 5.200 euros. Eso sugiere que Meta Ads está siendo
el principal motor de adquisición, mientras que Email ya tiene un peso relevante y probablemente
más rentable. Google Ads, en cambio, parece el canal con más necesidad de revisión o ajuste.

Plan de acción inmediato para las próximas dos semanas: revisa el rendimiento real de Google Ads
y compáralo con Meta Ads y Email en términos de coste por adquisición y revenue neto. Refuerza
las automatizaciones de Email, porque ya es un canal importante y puede crecer sin depender tanto
de inversión nueva. En paralelo, mejora la trazabilidad de costes para convertir el margen estimado
en un margen real y poder tomar decisiones con más precisión.

En resumen, el negocio está bien encaminado: crece, mantiene una operación sana y tiene canales
claramente identificables. La mayor oportunidad ahora no está en corregir una crisis, sino en optimizar
canales y afinar la medición de rentabilidad.
""",
        "fact_checks": [
            {
                "id": "estimated_margin_flag",
                "type": "classification",
                "accepted_terms": ["estimado", "margen estimado", "48,6", "interpretarlo con prudencia"],
            },
            {
                "id": "meta_main_channel",
                "type": "classification",
                "accepted_terms": ["meta ads lidera", "22.100", "22,100", "22100", "principal motor", "meta ads", "meta", "canal principal", "mayor revenue", "mayor facturacion"],
            },
            {
                "id": "google_needs_review",
                "type": "classification",
                "accepted_terms": ["google ads", "google", "5.200", "5,200", "5200", "muy por detras", "revision o ajuste", "menor revenue", "menor contribucion", "por debajo", "peor rendimiento"],
            },
            {
                "id": "positive_trend",
                "type": "trend",
                "accepted_terms": ["claramente positiva", "crece", "creci", "sube", "aument", "tendencia temporal", "positiv", "favorable", "evolucion"],
            },
        ],
    },
]
# case_06 — Negocio estacional con pico de ventas reciente
# Escenario: revenue alto pero concentrado, recompra buena, sin COGS, canales disponibles
BENCHMARK_CASES.append({
    "id": "case_06_seasonal_peak",
    "name": "Pico estacional con concentracion de revenue",
    "period": "last_90",
    "kpis": {
        "total_revenue":    {"value": 71400.0,  "growth_pct": 38.2,  "availability": "real"},
        "order_count":      {"value": 534.0,    "growth_pct": 29.4,  "availability": "real"},
        "avg_order_value":  {"value": 133.71,   "growth_pct": 6.8,   "availability": "real"},
        "net_revenue":      {"value": 66100.0,  "growth_pct": None,  "availability": "real"},
        "gross_margin_pct": {"value": None,     "growth_pct": None,  "availability": "missing"},
        "gross_margin":     {"value": None,     "growth_pct": None,  "availability": "missing"},
        "total_refunds":    {"value": 2140.0,   "growth_pct": None,  "availability": "real"},
        "refund_rate":      {"value": 3.0,      "growth_pct": None,  "availability": "real"},
        "unique_customers": {"value": 381.0,    "growth_pct": None,  "availability": "real"},
        "repeat_purchase_rate": {"value": 31.2, "growth_pct": None,  "availability": "real"},
        "avg_customer_ltv": {"value": 420.0,    "growth_pct": None,  "availability": "real"},
        "new_vs_returning": {"value": {"new": 262, "returning": 119}, "availability": "real"},
        "return_rate":      {"value": 4.8,      "growth_pct": None,  "availability": "real"},
        "returned_orders":  {"value": 25.0,     "growth_pct": None,  "availability": "real"},
        "avg_delivery_days":{"value": 3.1,      "growth_pct": None,  "availability": "real"},
        "delayed_orders_pct":{"value": 5.4,     "growth_pct": None,  "availability": "real"},
        "total_discounts":  {"value": 3160.0,   "growth_pct": None,  "availability": "real"},
        "discount_rate":    {"value": 4.4,      "growth_pct": None,  "availability": "real"},
    },
    "coverage": {
        "has_cogs": False, "has_channels": True, "has_countries": False,
        "has_returns": True, "has_discounts": True, "has_delivery": True,
        "has_customers": True, "has_categories": False, "has_products": False,
    },
    "charts": {
        "revenue_over_time": [
            {"label": "2024-01", "value": 12400.0},
            {"label": "2024-02", "value": 24600.0},
            {"label": "2024-03", "value": 34400.0},
        ],
        "orders_over_time": [
            {"label": "2024-01", "value": 94},
            {"label": "2024-02", "value": 184},
            {"label": "2024-03", "value": 256},
        ],
        "revenue_by_channel": [
            {"label": "Email",      "value": 28400.0},
            {"label": "Organic",    "value": 21600.0},
            {"label": "Meta Ads",   "value": 14800.0},
            {"label": "Google Ads", "value": 6600.0},
        ],
    },
    "reference_explanation": """
Tu negocio ha generado 71.400 euros en revenue bruto durante los últimos 90 días,
procesando 534 pedidos con un valor medio de 133,71 euros. El crecimiento es muy llamativo:
la facturación sube un 38,2%, los pedidos aumentan un 29,4% y el AOV mejora un 6,8%.
Sin embargo, la tendencia temporal revela que este crecimiento no es uniforme: el revenue
pasó de 12.400 euros en enero a 34.400 euros en marzo, lo que indica un pico de actividad
muy concentrado en el tramo final del periodo. Ese patrón puede responder a estacionalidad,
una campaña puntual o un evento concreto, y es importante entender si es sostenible
o si el negocio volverá a niveles más bajos en el siguiente periodo.

El revenue neto del periodo fue de 66.100 euros. Los descuentos representan el 4,4%
del revenue bruto, dentro del rango saludable. Los reembolsos fueron del 3%, también
por debajo del benchmark del 5%, lo que indica buena calidad en la entrega del producto.
No hay datos de margen bruto disponibles, así que no es posible evaluar la rentabilidad real
de este crecimiento. Ese es el dato que más falta hace ahora mismo.

En clientes, el negocio muestra señales muy positivas. De 381 clientes únicos, 119 son
recurrentes y la tasa de recompra alcanza el 31,2%, dentro de una banda normal-buena.
El LTV medio es de 420 euros, uno de los valores más altos vistos en este tipo de negocio,
lo que sugiere una base de clientes con valor real a largo plazo.

La operación está bien controlada: el tiempo medio de entrega es de 3,1 días,
rozando el nivel excelente, y solo el 5,4% de los pedidos llega con retraso.
En cuanto a canales, Email lidera con 28.400 euros, seguido de Organic con 21.600 euros.
Meta Ads aporta 14.800 euros y Google Ads solo 6.600 euros.

El riesgo principal aquí no es operativo ni de retención, sino de sostenibilidad:
un crecimiento del 38% concentrado en el último mes del periodo puede ser una señal excelente
o una distorsión estacional. Sin datos de margen, no puedes saber si ese pico fue rentable.

Plan de acción: incorpora COGS cuanto antes para saber si este crecimiento genera beneficio real,
analiza qué provocó el pico de marzo para saber si es replicable, y refuerza Email porque
ya es tu canal más rentable con 28.400 euros generados con bajo coste de adquisición.
""",
    "fact_checks": [
        {
            "id": "peak_concentration",
            "type": "trend",
            "accepted_terms": ["pico", "concentrad", "estacional", "marzo", "34.400", "34400", "crecimiento no es uniforme", "no uniforme"],
        },
        {
            "id": "email_main_channel",
            "type": "classification",
            "accepted_terms": ["email", "28.400", "28400", "canal principal", "lidera", "mayor revenue"],
        },
        {
            "id": "no_cogs_warning",
            "type": "classification",
            "accepted_terms": ["sin datos de margen", "no hay datos de margen", "margen no disponible", "no se puede evaluar", "cogs", "rentabilidad"],
        },
        {
            "id": "good_retention",
            "type": "classification",
            "accepted_terms": ["31,2", "31.2", "recompra", "recurrentes", "119", "normal"],
        },
    ],
})

# case_07 — Negocio en plateau: ventas estables sin crecimiento, margen excelente
# Escenario: el modelo debe identificar que no hay problema urgente pero si una oportunidad de escalar
BENCHMARK_CASES.append({
    "id": "case_07_plateau_excellent_margin",
    "name": "Plateau con margen excelente",
    "period": "last_90",
    "kpis": {
        "total_revenue":    {"value": 31200.0,  "growth_pct": 1.4,   "availability": "real"},
        "order_count":      {"value": 248.0,    "growth_pct": 0.8,   "availability": "real"},
        "avg_order_value":  {"value": 125.81,   "growth_pct": 0.6,   "availability": "real"},
        "net_revenue":      {"value": 29400.0,  "growth_pct": None,  "availability": "real"},
        "gross_margin_pct": {"value": 64.7,     "growth_pct": None,  "availability": "real"},
        "gross_margin":     {"value": 20186.0,  "growth_pct": None,  "availability": "real"},
        "total_refunds":    {"value": 870.0,    "growth_pct": None,  "availability": "real"},
        "refund_rate":      {"value": 2.8,      "growth_pct": None,  "availability": "real"},
        "unique_customers": {"value": 201.0,    "growth_pct": None,  "availability": "real"},
        "repeat_purchase_rate": {"value": 33.8, "growth_pct": None,  "availability": "real"},
        "avg_customer_ltv": {"value": 398.0,    "growth_pct": None,  "availability": "real"},
        "new_vs_returning": {"value": {"new": 133, "returning": 68}, "availability": "real"},
        "return_rate":      {"value": 3.6,      "growth_pct": None,  "availability": "real"},
        "returned_orders":  {"value": 9.0,      "growth_pct": None,  "availability": "real"},
        "avg_delivery_days":{"value": 2.8,      "growth_pct": None,  "availability": "real"},
        "delayed_orders_pct":{"value": 4.1,     "growth_pct": None,  "availability": "real"},
        "total_discounts":  {"value": 930.0,    "growth_pct": None,  "availability": "real"},
        "discount_rate":    {"value": 3.0,      "growth_pct": None,  "availability": "real"},
    },
    "coverage": {
        "has_cogs": True, "has_channels": False, "has_countries": False,
        "has_returns": True, "has_discounts": True, "has_delivery": True,
        "has_customers": True, "has_categories": False, "has_products": False,
    },
    "charts": {
        "revenue_over_time": [
            {"label": "2024-01", "value": 10300.0},
            {"label": "2024-02", "value": 10500.0},
            {"label": "2024-03", "value": 10400.0},
        ],
        "orders_over_time": [
            {"label": "2024-01", "value": 82},
            {"label": "2024-02", "value": 84},
            {"label": "2024-03", "value": 82},
        ],
    },
    "reference_explanation": """
Tu negocio ha generado 31.200 euros en revenue bruto durante los últimos 90 días,
procesando 248 pedidos con un valor medio de 125,81 euros. El crecimiento es prácticamente
nulo: la facturación sube solo un 1,4%, los pedidos un 0,8% y el AOV un 0,6%.
La tendencia temporal confirma esa estabilidad: el revenue se mueve entre 10.300 y 10.500
euros al mes sin variación significativa. El negocio está en un plateau.

Lo llamativo es que ese plateau se produce con unos fundamentos extraordinarios.
El margen bruto del 64,7% está por encima del nivel excelente en e-commerce, lo que significa
que de cada 100 euros que ingresas, 64,70 quedan después de cubrir el coste del producto.
En términos absolutos, el beneficio bruto del periodo fue de 20.186 euros, una cifra muy sólida
para un volumen de 248 pedidos. La tasa de reembolso del 2,8% y la tasa de devoluciones
del 3,6% están ambas por debajo del benchmark excelente del 5%.

La operación también es destacable: el tiempo medio de entrega es de 2,8 días, rozando
el nivel excelente, y solo el 4,1% de los pedidos llega con retraso. Los descuentos
representan apenas el 3% del revenue, muy por debajo del límite saludable.

En clientes, la tasa de recompra del 33,8% está en la parte alta de la banda normal,
con 68 clientes recurrentes sobre 201 únicos. El LTV medio de 398 euros es robusto.

El diagnóstico es claro: tienes un negocio muy bien construido que ha dejado de crecer.
No hay urgencias operativas ni problemas de rentabilidad. El reto es encontrar el palanca
que reactive el crecimiento sin comprometer los márgenes ni la calidad operativa.

Plan de acción: identifica qué limitó el crecimiento en los últimos tres meses,
si fue captación, producto o mercado. Con un margen del 64,7% puedes permitirte
invertir más en adquisición que la mayoría de tus competidores. Prueba aumentar
el presupuesto de captación un 20-30% este mes y mide si el AOV y el margen se mantienen.
""",
    "fact_checks": [
        {
            "id": "plateau_identified",
            "type": "classification",
            "accepted_terms": ["plateau", "estable", "sin crecimiento", "nulo", "1,4", "1.4", "practicamente plano"],
        },
        {
            "id": "excellent_margin",
            "type": "classification",
            "accepted_terms": ["64,7", "64.7", "excelente", "por encima", "extraordinario", "muy solido"],
        },
        {
            "id": "good_operations",
            "type": "classification",
            "accepted_terms": ["2,8", "2.8", "entrega", "excelente", "3,6", "3.6", "devoluciones"],
        },
        {
            "id": "growth_opportunity",
            "type": "classification",
            "accepted_terms": ["crecer", "crecimiento", "palanca", "oportunidad", "escalar", "reactivar", "captar"],
        },
    ],
})

# case_08 — Concentracion de producto: dependencia en 1-2 productos estrella
# Escenario: datos de productos disponibles, concentracion alta, margen variable por producto
BENCHMARK_CASES.append({
    "id": "case_08_product_concentration",
    "name": "Alta concentracion en producto estrella",
    "period": "last_90",
    "kpis": {
        "total_revenue":    {"value": 42600.0,  "growth_pct": 7.2,   "availability": "real"},
        "order_count":      {"value": 318.0,    "growth_pct": 5.1,   "availability": "real"},
        "avg_order_value":  {"value": 133.96,   "growth_pct": 2.0,   "availability": "real"},
        "net_revenue":      {"value": 39800.0,  "growth_pct": None,  "availability": "real"},
        "gross_margin_pct": {"value": 46.2,     "growth_pct": None,  "availability": "real"},
        "gross_margin":     {"value": 19681.0,  "growth_pct": None,  "availability": "real"},
        "total_refunds":    {"value": 1420.0,   "growth_pct": None,  "availability": "real"},
        "refund_rate":      {"value": 3.3,      "growth_pct": None,  "availability": "real"},
        "unique_customers": {"value": 263.0,    "growth_pct": None,  "availability": "real"},
        "repeat_purchase_rate": {"value": 24.7, "growth_pct": None,  "availability": "real"},
        "avg_customer_ltv": {"value": 310.0,    "growth_pct": None,  "availability": "real"},
        "new_vs_returning": {"value": {"new": 198, "returning": 65}, "availability": "real"},
        "return_rate":      {"value": 5.7,      "growth_pct": None,  "availability": "real"},
        "returned_orders":  {"value": 18.0,     "growth_pct": None,  "availability": "real"},
        "avg_delivery_days":{"value": 4.6,      "growth_pct": None,  "availability": "real"},
        "delayed_orders_pct":{"value": 7.8,     "growth_pct": None,  "availability": "real"},
        "total_discounts":  {"value": 1380.0,   "growth_pct": None,  "availability": "real"},
        "discount_rate":    {"value": 3.2,      "growth_pct": None,  "availability": "real"},
    },
    "coverage": {
        "has_cogs": True, "has_channels": False, "has_countries": False,
        "has_returns": True, "has_discounts": True, "has_delivery": True,
        "has_customers": True, "has_categories": True, "has_products": True,
    },
    "charts": {
        "revenue_over_time": [
            {"label": "2024-01", "value": 13400.0},
            {"label": "2024-02", "value": 14600.0},
            {"label": "2024-03", "value": 14600.0},
        ],
        "top_products_revenue": [
            {"label": "Producto Alpha", "value": 21800.0},
            {"label": "Producto Beta",  "value": 9400.0},
            {"label": "Producto Gamma", "value": 5200.0},
            {"label": "Producto Delta", "value": 3800.0},
            {"label": "Otros",          "value": 2400.0},
        ],
        "revenue_by_category": [
            {"label": "Premium",  "value": 31200.0},
            {"label": "Estandar", "value": 8600.0},
            {"label": "Basico",   "value": 2800.0},
        ],
        "product_margin": [
            {"label": "Producto Alpha", "value": 58.2},
            {"label": "Producto Beta",  "value": 41.4},
            {"label": "Producto Gamma", "value": 33.1},
            {"label": "Producto Delta", "value": 28.7},
        ],
    },
    "reference_explanation": """
Tu negocio ha generado 42.600 euros en revenue bruto durante los últimos 90 días,
procesando 318 pedidos con un valor medio de 133,96 euros. El crecimiento es moderado
pero consistente: facturación sube un 7,2%, pedidos un 5,1% y AOV un 2%.
La tendencia muestra estabilización en los dos últimos meses en torno a 14.600 euros.

El margen bruto del 46,2% está en la banda normal del sector y el beneficio bruto
del periodo fue de 19.681 euros. Los reembolsos al 3,3% y las devoluciones al 5,7%
están bajo control, aunque las devoluciones están ligeramente por encima del benchmark
excelente del 5%.

El dato más importante de este análisis son los productos. Producto Alpha concentra
21.800 euros, lo que representa el 51,2% de todo el revenue del negocio. Además,
es el producto con mayor margen: 58,2% frente al 28,7% de Producto Delta.
Esta concentración es un riesgo real: si Producto Alpha tiene un problema de stock,
un competidor lo copia o cambia la demanda, más de la mitad del negocio se ve afectada.
La categoría Premium, donde se encuadra principalmente, representa 31.200 euros,
el 73,2% del revenue total.

La dependencia de un producto con márgenes altos puede parecer positiva a corto plazo,
pero hace el negocio frágil. Los productos Gamma y Delta tienen márgenes del 33,1%
y 28,7% respectivamente, por debajo del mínimo recomendable del 40%.

Plan de acción: diversifica el catálogo desarrollando 1-2 productos nuevos en la
categoría Premium que complementen a Producto Alpha. Revisa los precios o costes
de Gamma y Delta para acercar su margen al 40%. Aprovecha la base de clientes
recurrentes para hacer cross-selling hacia Producto Beta, que ya tiene margen del 41,4%.
""",
    "fact_checks": [
        {
            "id": "product_alpha_dominant",
            "type": "classification",
            "accepted_terms": ["producto alpha", "alpha", "21.800", "21800", "51", "concentra", "concentracion", "mayor revenue"],
        },
        {
            "id": "concentration_risk",
            "type": "classification",
            "accepted_terms": ["riesgo", "dependencia", "concentracion", "fragil", "mitad del negocio", "50%", "51%"],
        },
        {
            "id": "alpha_best_margin",
            "type": "classification",
            "accepted_terms": ["58,2", "58.2", "mejor margen", "mayor margen", "alpha"],
        },
        {
            "id": "premium_category",
            "type": "classification",
            "accepted_terms": ["premium", "31.200", "31200", "73", "categoria"],
        },
    ],
})

# case_09 — Negocio premium con AOV muy alto y volumen bajo
# Escenario: pocos pedidos, tickets altos, LTV excelente, reto de captacion
BENCHMARK_CASES.append({
    "id": "case_09_premium_low_volume",
    "name": "Negocio premium con volumen bajo",
    "period": "last_90",
    "kpis": {
        "total_revenue":    {"value": 38400.0,  "growth_pct": 9.8,   "availability": "real"},
        "order_count":      {"value": 96.0,     "growth_pct": 6.7,   "availability": "real"},
        "avg_order_value":  {"value": 400.0,    "growth_pct": 2.9,   "availability": "real"},
        "net_revenue":      {"value": 36200.0,  "growth_pct": None,  "availability": "real"},
        "gross_margin_pct": {"value": 61.4,     "growth_pct": None,  "availability": "real"},
        "gross_margin":     {"value": 23578.0,  "growth_pct": None,  "availability": "real"},
        "total_refunds":    {"value": 1100.0,   "growth_pct": None,  "availability": "real"},
        "refund_rate":      {"value": 2.9,      "growth_pct": None,  "availability": "real"},
        "unique_customers": {"value": 84.0,     "growth_pct": None,  "availability": "real"},
        "repeat_purchase_rate": {"value": 38.1, "growth_pct": None,  "availability": "real"},
        "avg_customer_ltv": {"value": 980.0,    "growth_pct": None,  "availability": "real"},
        "new_vs_returning": {"value": {"new": 52, "returning": 32},  "availability": "real"},
        "return_rate":      {"value": 4.2,      "growth_pct": None,  "availability": "real"},
        "returned_orders":  {"value": 4.0,      "growth_pct": None,  "availability": "real"},
        "avg_delivery_days":{"value": 5.2,      "growth_pct": None,  "availability": "real"},
        "delayed_orders_pct":{"value": 9.4,     "growth_pct": None,  "availability": "real"},
        "total_discounts":  {"value": 1100.0,   "growth_pct": None,  "availability": "real"},
        "discount_rate":    {"value": 2.9,      "growth_pct": None,  "availability": "real"},
    },
    "coverage": {
        "has_cogs": True, "has_channels": False, "has_countries": False,
        "has_returns": True, "has_discounts": True, "has_delivery": True,
        "has_customers": True, "has_categories": False, "has_products": False,
    },
    "charts": {
        "revenue_over_time": [
            {"label": "2024-01", "value": 11800.0},
            {"label": "2024-02", "value": 12600.0},
            {"label": "2024-03", "value": 14000.0},
        ],
        "orders_over_time": [
            {"label": "2024-01", "value": 29},
            {"label": "2024-02", "value": 32},
            {"label": "2024-03", "value": 35},
        ],
    },
    "reference_explanation": """
Tu negocio ha generado 38.400 euros en revenue bruto durante los últimos 90 días,
procesando 96 pedidos con un valor medio de 400 euros por pedido. El crecimiento
es positivo y acelerado: facturación sube un 9,8%, pedidos un 6,7% y AOV un 2,9%.
La tendencia temporal es consistente al alza: el revenue ha pasado de 11.800 euros
en enero a 14.000 euros en marzo, con los pedidos subiendo de 29 a 35.

Este es un negocio de ticket alto y volumen reducido. Un AOV de 400 euros está
muy por encima de la media del sector e-commerce y refleja un posicionamiento
premium o un catálogo de producto de alto valor. El margen bruto del 61,4%
está en zona excelente, con un beneficio bruto del periodo de 23.578 euros.

Los indicadores de cliente son extraordinarios. La tasa de recompra del 38,1%
supera el benchmark excelente del 35%, con 32 clientes recurrentes sobre 84 únicos.
El LTV medio por cliente es de 980 euros, un valor muy elevado que confirma
que los clientes que compran una vez tienden a repetir y gastar mucho.
El ratio LTV/AOV es de 2,45x, todavía por debajo del benchmark de 3x,
pero con la tendencia actual puede alcanzarlo en 2-3 periodos.

La tasa de devoluciones del 4,2% y los reembolsos al 2,9% están ambos en zona excelente.
El tiempo medio de entrega de 5,2 días es aceptable para un producto premium,
aunque el 9,4% de pedidos con retraso está cerca del umbral del 10% y merece atención.

El único riesgo estructural es el volumen: con 96 pedidos en 90 días, el negocio
es sensible a la pérdida de cualquier cliente recurrente. Una caída de 5-6 clientes
clave puede impactar el revenue de forma visible. La captación de nuevos clientes
premium es el reto principal.

Plan de acción: con un LTV de 980 euros puedes permitirte invertir hasta 200-250 euros
por cliente nuevo y seguir siendo rentable. Activa campañas de captación segmentadas
dirigidas al perfil de cliente premium, refuerza el programa de fidelización para
proteger a los 32 clientes recurrentes actuales y trabaja para reducir los retrasos
logísticos por debajo del 7%.
""",
    "fact_checks": [
        {
            "id": "high_aov",
            "type": "classification",
            "accepted_terms": ["400", "aov", "ticket alto", "ticket medio", "valor medio", "premium"],
        },
        {
            "id": "excellent_retention",
            "type": "classification",
            "accepted_terms": ["38,1", "38.1", "excelente", "35%", "supera", "recompra"],
        },
        {
            "id": "high_ltv",
            "type": "classification",
            "accepted_terms": ["980", "ltv", "valor por cliente", "extraordinario", "elevado"],
        },
        {
            "id": "volume_risk",
            "type": "classification",
            "accepted_terms": ["volumen", "96 pedidos", "sensible", "riesgo", "captacion", "pocos pedidos"],
        },
    ],
})

# case_10 — Dataset completo: todos los KPIs, geografia, categorias y canales
# Escenario: maximo de informacion disponible, el modelo debe aprovecharla toda
BENCHMARK_CASES.append({
    "id": "case_10_full_dataset",
    "name": "Dataset completo con todas las dimensiones",
    "period": "last_90",
    "kpis": {
        "total_revenue":    {"value": 63800.0,  "growth_pct": 11.3,  "availability": "real"},
        "order_count":      {"value": 482.0,    "growth_pct": 8.6,   "availability": "real"},
        "avg_order_value":  {"value": 132.37,   "growth_pct": 2.5,   "availability": "real"},
        "net_revenue":      {"value": 58900.0,  "growth_pct": None,  "availability": "real"},
        "gross_margin_pct": {"value": 49.8,     "growth_pct": None,  "availability": "real"},
        "gross_margin":     {"value": 31772.0,  "growth_pct": None,  "availability": "real"},
        "total_refunds":    {"value": 2100.0,   "growth_pct": None,  "availability": "real"},
        "refund_rate":      {"value": 3.3,      "growth_pct": None,  "availability": "real"},
        "unique_customers": {"value": 341.0,    "growth_pct": None,  "availability": "real"},
        "repeat_purchase_rate": {"value": 29.6, "growth_pct": None,  "availability": "real"},
        "avg_customer_ltv": {"value": 356.0,    "growth_pct": None,  "availability": "real"},
        "new_vs_returning": {"value": {"new": 240, "returning": 101}, "availability": "real"},
        "return_rate":      {"value": 5.2,      "growth_pct": None,  "availability": "real"},
        "returned_orders":  {"value": 25.0,     "growth_pct": None,  "availability": "real"},
        "avg_delivery_days":{"value": 3.9,      "growth_pct": None,  "availability": "real"},
        "delayed_orders_pct":{"value": 6.8,     "growth_pct": None,  "availability": "real"},
        "total_discounts":  {"value": 2800.0,   "growth_pct": None,  "availability": "real"},
        "discount_rate":    {"value": 4.4,      "growth_pct": None,  "availability": "real"},
    },
    "coverage": {
        "has_cogs": True, "has_channels": True, "has_countries": True,
        "has_returns": True, "has_discounts": True, "has_delivery": True,
        "has_customers": True, "has_categories": True, "has_products": True,
    },
    "charts": {
        "revenue_over_time": [
            {"label": "2024-01", "value": 19200.0},
            {"label": "2024-02", "value": 21400.0},
            {"label": "2024-03", "value": 23200.0},
        ],
        "revenue_by_channel": [
            {"label": "Organic",    "value": 24600.0},
            {"label": "Email",      "value": 18900.0},
            {"label": "Meta Ads",   "value": 13200.0},
            {"label": "Google Ads", "value": 7100.0},
        ],
        "revenue_by_country": [
            {"label": "ES", "value": 38200.0},
            {"label": "MX", "value": 12400.0},
            {"label": "AR", "value": 7600.0},
            {"label": "CO", "value": 3800.0},
            {"label": "CL", "value": 1800.0},
        ],
        "revenue_by_category": [
            {"label": "Hogar",     "value": 28400.0},
            {"label": "Moda",      "value": 19600.0},
            {"label": "Deporte",   "value": 10200.0},
            {"label": "Otros",     "value": 5600.0},
        ],
        "top_products_revenue": [
            {"label": "Producto A", "value": 14200.0},
            {"label": "Producto B", "value": 11800.0},
            {"label": "Producto C", "value": 9400.0},
            {"label": "Producto D", "value": 7600.0},
            {"label": "Producto E", "value": 6200.0},
        ],
    },
    "reference_explanation": """
Tu negocio ha generado 63.800 euros en revenue bruto durante los últimos 90 días,
procesando 482 pedidos con un valor medio de 132,37 euros. El crecimiento es sólido
y uniforme: la facturación sube un 11,3%, los pedidos un 8,6% y el AOV un 2,5%.
La tendencia temporal confirma la progresión: el revenue ha pasado de 19.200 euros
en enero a 23.200 euros en marzo, un crecimiento del 20,8% en tres meses.

El margen bruto del 49,8% está en la parte media-alta del rango normal del sector,
con un beneficio bruto del periodo de 31.772 euros. El revenue neto fue de 58.900 euros.
Los descuentos representan el 4,4% del revenue, dentro del rango saludable,
y los reembolsos son del 3,3%, también por debajo del benchmark del 5%.

En canales, Organic lidera con 24.600 euros, seguido de Email con 18.900 euros.
Meta Ads aporta 13.200 euros y Google Ads 7.100 euros. La fortaleza del canal
Organic es una ventaja competitiva real: genera revenue sin coste directo por visita.

Geográficamente, España concentra 38.200 euros, el 59,9% del total. México aporta
12.400 euros y Argentina 7.600 euros. La presencia en Latinoamérica ya representa
el 40% del revenue y puede ser un vector de crecimiento importante.

En producto, la categoría Hogar lidera con 28.400 euros. Producto A es el más vendido
con 14.200 euros y Producto B con 11.800 euros. La distribución es más equilibrada
que en negocios con alta concentración, lo que reduce el riesgo de dependencia.

La tasa de recompra del 29,6% está en la banda normal y el LTV medio por cliente
es de 356 euros. La tasa de devoluciones del 5,2% y el 6,8% de pedidos retrasados
son aceptables pero tienen margen de mejora.

Plan de acción: refuerza el posicionamiento en México y Argentina que ya representan
el 40% del revenue, invierte en SEO para proteger y crecer el canal Organic,
y trabaja en reducir los retrasos logísticos por debajo del 5% para proteger
la satisfacción en mercados internacionales donde las expectativas son más exigentes.
""",
    "fact_checks": [
        {
            "id": "organic_leads",
            "type": "classification",
            "accepted_terms": ["organic", "24.600", "24600", "lidera", "canal principal", "mayor revenue"],
        },
        {
            "id": "spain_dominant",
            "type": "classification",
            "accepted_terms": ["es", "españa", "38.200", "38200", "59", "60%", "principal mercado"],
        },
        {
            "id": "latam_opportunity",
            "type": "classification",
            "accepted_terms": ["mexico", "argentina", "latam", "latinoamerica", "40%", "internacional", "crecimiento"],
        },
        {
            "id": "hogar_category",
            "type": "classification",
            "accepted_terms": ["hogar", "28.400", "28400", "categoria", "lidera"],
        },
    ],
})