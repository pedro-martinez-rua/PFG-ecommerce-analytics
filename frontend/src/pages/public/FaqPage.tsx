import { useState } from 'react';
import { Link } from '@/components/Link';
import { BarChart3, Upload, Sparkles, Shield, Users, HelpCircle } from 'lucide-react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

const FAQ_DATA = [
  {
    category: 'Empezando',
    icon: Upload,
    items: [
      {
        id: 'q1',
        question: '¿Qué formatos de archivo acepta la plataforma?',
        answer: 'Aceptamos ficheros CSV y Excel (.xlsx). El sistema detecta automáticamente el separador (coma, punto y coma o tabulador) y el encoding (UTF-8, Latin-1). No es necesario formatear el fichero de ninguna manera especial: el pipeline de ingesta se adapta a la mayoría de exportaciones estándar de plataformas como Shopify, WooCommerce, Amazon o cualquier ERP.',
      },
      {
        id: 'q2',
        question: '¿Necesito que mi fichero tenga una cabecera específica?',
        answer: 'No. El sistema usa fuzzy matching para reconocer los nombres de columna aunque estén en español, inglés, con abreviaciones o con pequeñas variaciones. Si el fichero no tiene cabecera, el pipeline infiere automáticamente qué contiene cada columna analizando los datos. Lo único que necesitas es que los datos sean consistentes dentro de cada columna.',
      },
      {
        id: 'q3',
        question: '¿Qué pasa si mi fichero tiene errores o filas inválidas?',
        answer: 'El sistema valida cada fila individualmente. Las filas con errores (fechas inválidas, precios negativos, campos obligatorios vacíos) se marcan como inválidas y se excluyen del análisis, pero no bloquean la ingesta. En la página de imports puedes ver exactamente cuántas filas fueron válidas e inválidas por cada fichero.',
      },
      {
        id: 'q4',
        question: '¿Puedo subir varios ficheros del mismo negocio?',
        answer: 'Sí, y es la forma recomendada de trabajar. Puedes subir por separado los ficheros de pedidos, líneas de pedido, clientes y productos. Al crear un dashboard, el sistema los combina automáticamente y resuelve las relaciones entre ellos. También puedes subir datos de distintos periodos y el sistema los agrega correctamente.',
      },
    ],
  },
  {
    category: 'Dashboards y análisis',
    icon: BarChart3,
    items: [
      {
        id: 'q5',
        question: '¿Cómo funciona la creación de un dashboard?',
        answer: 'El proceso tiene tres pasos: primero subes uno o varios ficheros de datos, luego creas un dashboard seleccionando los ficheros que quieres analizar y dándole un nombre, y finalmente el sistema calcula automáticamente todos los KPIs y genera las gráficas correspondientes. Desde el dashboard puedes guardar un informe con un snapshot de los datos y el análisis de IA.',
      },
      {
        id: 'q6',
        question: '¿Qué KPIs calcula la plataforma?',
        answer: 'El sistema calcula automáticamente los KPIs disponibles según los datos que hayas subido. Incluye métricas de ventas (revenue total, AOV, pedidos), rentabilidad (margen bruto, descuentos, reembolsos), clientes (clientes únicos, tasa de recompra, LTV medio, nuevos vs. recurrentes) y operación (tasa de devoluciones, días de entrega, pedidos retrasados). Cada KPI indica si es un dato real, estimado o si faltan datos para calcularlo.',
      },
      {
        id: 'q7',
        question: '¿Puedo combinar datos de distintos periodos en un mismo dashboard?',
        answer: 'Sí. Al crear un dashboard y seleccionar varios ficheros con distintos rangos de fechas, el sistema calcula automáticamente el rango combinado y agrega todos los datos. Esto es útil por ejemplo para combinar exportaciones mensuales o trimestrales en un análisis anual.',
      },
      {
        id: 'q8',
        question: '¿Qué son los informes guardados?',
        answer: 'Un informe es un snapshot de un dashboard en un momento concreto. Incluye los valores de todos los KPIs calculados y el análisis de IA generado por el sistema. Los informes se almacenan permanentemente y puedes consultarlos en cualquier momento desde la sección de Informes guardados, aunque añadas más datos posteriormente.',
      },
    ],
  },
  {
    category: 'Análisis con IA',
    icon: Sparkles,
    items: [
      {
        id: 'q9',
        question: '¿Cómo funciona el análisis de IA?',
        answer: 'El sistema envía únicamente métricas agregadas (sin datos personales) a un modelo de lenguaje especializado en análisis de negocio. El modelo interpreta los KPIs en contexto, los compara con benchmarks del sector e-commerce y genera recomendaciones específicas y accionables para tu negocio. El análisis está diseñado para ser útil incluso sin conocimientos técnicos de datos.',
      },
      {
        id: 'q10',
        question: '¿El análisis de IA accede a mis datos personales?',
        answer: 'No. Por diseño, el sistema nunca envía datos personales al modelo de IA. Solo se transmiten métricas agregadas como "revenue total: 45.000€", "tasa de recompra: 18%", etc. Los datos individuales de clientes, pedidos o productos permanecen únicamente en tu base de datos.',
      },
      {
        id: 'q11',
        question: '¿Qué tipo de recomendaciones da el análisis de IA?',
        answer: 'El análisis identifica los puntos fuertes y débiles de tu negocio basándose en tus datos y los compara con benchmarks del sector. Las recomendaciones son concretas y accionables: por ejemplo, si la tasa de recompra es baja, el sistema no solo lo detecta sino que propone acciones específicas como enviar un email de reactivación a clientes con más de 60 días sin comprar, con un resultado estimado realista.',
      },
    ],
  },
  {
    category: 'Seguridad y privacidad',
    icon: Shield,
    items: [
      {
        id: 'q12',
        question: '¿Cómo se protegen mis datos?',
        answer: 'La plataforma utiliza una arquitectura multi-tenant donde cada empresa tiene sus datos completamente aislados. El acceso está protegido con autenticación JWT y todos los endpoints verifican que el usuario solo puede acceder a los datos de su propia empresa. Ningún usuario puede ver los datos de otra empresa bajo ninguna circunstancia.',
      },
      {
        id: 'q13',
        question: '¿Puedo eliminar mis datos?',
        answer: 'Sí. Puedes eliminar cualquier import desde la sección de Imports, y la eliminación es en cascada: se borran todos los pedidos, líneas, clientes y productos asociados a ese fichero. También puedes eliminar dashboards e informes de forma individual. Si quieres eliminar todos tus datos, puedes hacerlo desde el perfil.',
      },
      {
        id: 'q14',
        question: '¿Quién puede acceder a mi cuenta?',
        answer: 'Solo los usuarios que tú hayas registrado con el email y contraseña de tu empresa. El sistema no tiene acceso de administrador a los datos de los clientes, y los análisis de IA se realizan con datos anonimizados. Cada sesión expira automáticamente por seguridad.',
      },
    ],
  },
  {
    category: 'Cuenta y uso',
    icon: Users,
    items: [
      {
        id: 'q15',
        question: '¿Para qué tipo de negocio está pensada la plataforma?',
        answer: 'La plataforma está diseñada para pequeñas y medianas empresas de e-commerce, autónomos con tienda online y emprendedores digitales que quieren entender sus datos de ventas sin necesitar conocimientos técnicos de análisis de datos ni contratar un analista. Es especialmente útil si exportas datos de Shopify, WooCommerce, Amazon o cualquier plataforma de venta online.',
      },
      {
        id: 'q16',
        question: '¿Cuántos ficheros puedo subir?',
        answer: 'No hay límite en el número de ficheros que puedes subir. Puedes subir tantos ficheros como necesites e ir creando distintos dashboards combinando los que quieras analizar juntos. El límite de tamaño por fichero es de 50MB.',
      },
      {
        id: 'q17',
        question: '¿Tengo algún problema si no tengo experiencia con datos?',
        answer: 'No. La plataforma está diseñada específicamente para usuarios sin experiencia técnica. No necesitas saber qué es un KPI, cómo se calcula el margen bruto ni qué significa LTV: el sistema calcula todo automáticamente y el análisis de IA lo explica en lenguaje claro y con recomendaciones concretas. Solo necesitas tener los datos de tu negocio en un fichero CSV o Excel.',
      },
    ],
  },
];

export function FaqPage() {
  const [openCategory, setOpenCategory] = useState<string | null>('Empezando');

  return (
    <div className="py-16">
      <div className="container max-w-3xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-secondary/10 mb-4">
            <HelpCircle className="h-6 w-6 text-secondary" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Preguntas frecuentes
          </h1>
          <p className="text-muted-foreground text-lg">
            Todo lo que necesitas saber para sacar el máximo partido a tus datos de negocio.
          </p>
        </div>

        {/* FAQ por categorías */}
        <div className="space-y-8">
          {FAQ_DATA.map(({ category, icon: Icon, items }) => (
            <div key={category}>
              <button
                onClick={() => setOpenCategory(openCategory === category ? null : category)}
                className="flex items-center gap-3 w-full text-left mb-4 group"
              >
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-secondary/10">
                  <Icon className="h-4 w-4 text-secondary" />
                </div>
                <h2 className="text-lg font-semibold text-foreground group-hover:text-secondary transition-colors">
                  {category}
                </h2>
                <span className="ml-auto text-xs text-muted-foreground">
                  {items.length} preguntas
                </span>
              </button>

              {openCategory === category && (
                <Accordion type="single" collapsible className="space-y-2">
                  {items.map(faq => (
                    <AccordionItem
                      key={faq.id}
                      value={faq.id}
                      className="border rounded-lg px-4"
                    >
                      <AccordionTrigger className="text-left hover:no-underline py-4">
                        <span className="font-medium text-foreground">{faq.question}</span>
                      </AccordionTrigger>
                      <AccordionContent className="pb-4 text-muted-foreground leading-relaxed">
                        {faq.answer}
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              )}
            </div>
          ))}
        </div>

        {/* Footer CTA */}
        <div className="mt-12 text-center bg-muted/50 rounded-xl p-8">
          <p className="font-medium text-foreground mb-2">
            ¿No encuentras lo que buscas?
          </p>
          <p className="text-sm text-muted-foreground mb-4">
            Escríbenos y te respondemos en menos de 24 horas.
          </p>
          <Link
            href="/contact"
            className="text-secondary hover:text-secondary font-medium underline underline-offset-4"
          >
            Contactar con soporte →
          </Link>
        </div>
      </div>
    </div>
  );
}