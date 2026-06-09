import { useState, useEffect, useRef } from 'react';
import {
  Upload, LayoutDashboard, FileText, Sparkles,
  CheckCircle2, ChevronRight, Info,
  UserPlus, Settings, BarChart3, ArrowRight, Users
} from 'lucide-react';

/* Types */

interface Step {
  title: string;
  description: string;
  tip?: string;
  image: string;
  imageAlt: string;
}

interface Section {
  id: string;
  icon: React.ElementType;
  title: string;
  subtitle: string;
  steps: Step[];
}

/* Data */

const SECTIONS: Section[] = [
  {
    id: 'primeros-pasos',
    icon: UserPlus,
    title: 'Primeros pasos',
    subtitle: 'Crea tu cuenta, configura tu perfil y explora el panel inicial.',
    steps: [
      {
        title: 'Regístrate en CommerceIQ',
        description:
          'Accede a la página de registro e introduce tu nombre, email y contraseña. Al crear la cuenta se genera automáticamente un tenant aislado para tu negocio — ningún otro usuario tendrá acceso a tus datos.',
        tip: 'Usa un email corporativo si compartes la plataforma con tu equipo.',
        image: '/tutorials/01-PrimerosPasos/01-register.png',
        imageAlt: 'Pantalla de registro de CommerceIQ',
      },
      {
        title: 'Configura tu perfil y empresa',
        description:
          'Ve a "Perfil y ajustes" desde el menú lateral. Aquí puedes cambiar tu nombre, email, contraseña e idioma de la interfaz.',
        image: '/tutorials/01-PrimerosPasos/02-profile.png',
        imageAlt: 'Página de Perfil y ajustes',
      },
      {
        title: 'Explora el Resumen inicial',
        description:
          'Nada más entrar verás la página "Resumen". Es tu punto de partida: muestra el estado general de la plataforma y te guía hacia los siguientes pasos cuando aún no tienes datos cargados.',
        image: '/tutorials/01-PrimerosPasos/03-resumen.png',
        imageAlt: 'Página Resumen vacía con onboarding',
      },
    ],
  },
  {
    id: 'imports',
    icon: Upload,
    title: 'Subir e importar datos',
    subtitle: 'Carga archivos CSV o Excel con tus datos de pedidos y revisa el diagnóstico.',
    steps: [
      {
        title: 'Ve a "Subir datos" y selecciona tu archivo',
        description:
          'Haz clic en "Subir datos" en el menú lateral. Arrastra el archivo a la zona de carga o haz clic en "Seleccionar archivo". Se aceptan CSV (.csv) y Excel (.xlsx).',
        tip: 'Exporta el historial de pedidos desde tu tienda (Shopify, WooCommerce, etc.). No es necesario que las columnas tengan nombres exactos — el sistema los detecta automáticamente.',
        image: '/tutorials/02-Imports/01-subirdatos.png',
        imageAlt: 'Página Subir datos con área de drop',
      },
      {
        title: 'Revisa los datos subidos',
        description:
          'Una vez cargado, el sistema muestra un resumen del archivo: nombre, número de filas y estado de validación. Puedes ver qué archivos has importado en cualquier momento desde la sección Imports.',
        image: '/tutorials/02-Imports/02-datossubidos.png',
        imageAlt: 'Resumen de datos subidos',
      },
      {
        title: 'Revisa el diagnóstico de columnas',
        description:
          'Antes de confirmar la importación verás un resumen de las columnas detectadas, el número de filas válidas y posibles advertencias (campos vacíos, fechas con formatos mixtos, etc.).',
        tip: 'Si el sistema no detecta bien alguna columna, el ETL incluye inferencia por contenido — en la mayoría de casos se resuelve automáticamente.',
        image: '/tutorials/02-Imports/03-RevisionColumnas.png',
        imageAlt: 'Diagnóstico de columnas detectadas',
      },
      {
        title: 'Confirma la importación',
        description:
          'Al confirmar, el pipeline ETL procesa el archivo: limpia, normaliza y almacena los registros. El import queda guardado en "Imports" para consultarlo en cualquier momento.',
        image: '/tutorials/02-Imports/04-ColumnasRevisadas.png',
        imageAlt: 'Confirmación de importación exitosa',
      },
    ],
  },
  {
    id: 'dashboards',
    icon: LayoutDashboard,
    title: 'Crear y explorar dashboards',
    subtitle: 'Genera dashboards de KPIs a partir de tus imports con filtros de fecha y análisis de IA.',
    steps: [
      {
        title: 'Accede a Dashboards y crea uno nuevo',
        description:
          'Desde el menú lateral accede a "Dashboards". Haz clic en "Nuevo dashboard", elige un nombre descriptivo y selecciona los imports que quieres incluir. Puedes combinar varios para unir datos de distintos períodos.',
        image: '/tutorials/03-Dashboards/01-Dashboard.png',
        imageAlt: 'Página de Dashboards',
      },
      {
        title: 'Configura el nuevo dashboard',
        description:
          'El asistente de creación te muestra todos tus imports disponibles. Selecciona uno o varios y ajusta el rango de fechas para acotar el análisis a la semana, mes, trimestre o rango personalizado que necesites.',
        tip: 'Selecciona imports del mismo tipo de datos para que los KPIs sean coherentes.',
        image: '/tutorials/03-Dashboards/02-NuevoDashboard.png',
        imageAlt: 'Wizard de creación de dashboard',
      },
      {
        title: 'Filtra por fechas',
        description:
          'Una vez creado, puedes ajustar el período de análisis en cualquier momento usando los filtros de fecha en la parte superior del dashboard. Los KPIs y gráficas se recalculan al instante.',
        image: '/tutorials/03-Dashboards/03-FiltroFechasDash.png',
        imageAlt: 'Selector de rango de fechas en el dashboard',
      },
      {
        title: 'Consulta el análisis de IA integrado',
        description:
          'Cada dashboard incluye un panel de análisis generado por IA con Groq que interpreta los KPIs calculados y ofrece un resumen ejecutivo, tendencias detectadas y recomendaciones.',
        image: '/tutorials/03-Dashboards/04-AnalisisIA.png',
        imageAlt: 'Panel de análisis de IA en el dashboard',
      },
      {
        title: 'Expande el análisis completo',
        description:
          'Despliega el panel de IA para leer el análisis completo con todas las secciones estructuradas: rendimiento general, oportunidades de mejora y próximos pasos recomendados.',
        image: '/tutorials/03-Dashboards/05-DesplegableIA.png',
        imageAlt: 'Análisis de IA expandido',
      },
    ],
  },
  {
    id: 'informes',
    icon: FileText,
    title: 'Informes guardados',
    subtitle: 'Genera, guarda y consulta informes con insights de IA vinculados a cada dashboard.',
    steps: [
      {
        title: 'Genera un informe desde un dashboard',
        description:
          'Desde cualquier dashboard activo, haz clic en el botón "Guardar informe". El sistema toma un snapshot de los KPIs y gráficas actuales y lo vincula con el análisis de IA.',
        tip: 'El informe queda guardado automáticamente. Puedes consultarlo en cualquier momento sin regenerar los datos.',
        image: '/tutorials/04-Informe/01-CrearInforme.png',
        imageAlt: 'Botón de guardar informe en el dashboard',
      },
      {
        title: 'Consulta el detalle del informe',
        description:
          'Haz clic en un informe para ver su detalle completo: KPIs agrupados por categoría (ventas, rentabilidad, clientes, operación), gráficas históricas y el análisis de IA renderizado.',
        image: '/tutorials/04-Informe/02-VerInforme.png',
        imageAlt: 'Vista detalle de un informe',
      },
      {
        title: 'Gestiona tus informes guardados',
        description:
          'En "Informes guardados" se listan todos los informes generados con su fecha, período analizado y KPIs principales. Puedes compartirlos con el equipo o eliminarlos desde aquí.',
        image: '/tutorials/04-Informe/03-InformesGuardados.png',
        imageAlt: 'Página de Informes guardados',
      },
      {
        title: 'Lee el análisis completo',
        description:
          'El informe presenta el análisis de IA en formato estructurado con secciones claramente diferenciadas: resumen ejecutivo, tendencias, riesgos y recomendaciones accionables.',
        image: '/tutorials/04-Informe/04-VistaInforme.png',
        imageAlt: 'Vista completa de informe con análisis de IA',
      },
    ],
  },
  {
    id: 'equipo',
    icon: Users,
    title: 'Gestión del equipo',
    subtitle: 'Añade miembros, gestiona accesos y comparte informes con tu organización.',
    steps: [
      {
        title: 'Accede a la sección Equipo',
        description:
          'En el menú lateral encontrarás "Equipo". Aquí se muestran todos los informes compartidos por los miembros de tu organización. Solo los usuarios con acceso activado pueden verlos.',
        image: '/tutorials/05-Team/01-GestionarEquipo.png',
        imageAlt: 'Página Equipo con informes compartidos',
      },
      {
        title: 'Gestiona miembros como administrador',
        description:
          'Desde "Perfil → Miembros" el administrador puede ver todos los usuarios del tenant, activar o desactivar su acceso a la pantalla de Equipo, y eliminarlos si es necesario.',
        tip: 'Solo los administradores pueden gestionar el acceso de los miembros. Los analistas solo pueden ver los informes compartidos.',
        image: '/tutorials/05-Team/02-AdminGestion.png',
        imageAlt: 'Panel de gestión de miembros',
      },
      {
        title: 'Comparte un informe con el equipo',
        description:
          'Desde "Informes guardados", el administrador puede activar la opción "Compartir con equipo" en cualquier informe. El informe aparecerá entonces en la sección Equipo para todos los miembros con acceso.',
        image: '/tutorials/05-Team/03-CompartirInformeAdmin.png',
        imageAlt: 'Botón de compartir informe con el equipo',
      },
      {
        title: 'Vista del analista en Equipo',
        description:
          'Los miembros con acceso a Team ven en la sección Equipo todos los informes compartidos por el administrador, con el nombre del creador, el período analizado y los KPIs principales.',
        image: '/tutorials/05-Team/04-AnalistaEquipo.png',
        imageAlt: 'Vista de la sección Equipo desde una cuenta de analista',
      },
      {
        title: 'El analista accede al informe completo',
        description:
          'Al hacer clic en un informe compartido, el analista puede ver el snapshot completo — KPIs, gráficas y análisis de IA — sin necesidad de tener los datos originales cargados en su cuenta.',
        image: '/tutorials/05-Team/05-VistaAnalistaInforme.png',
        imageAlt: 'Analista viendo el detalle de un informe compartido',
      },
    ],
  },
];

/* Screenshot component */

function Screenshot({ src, alt }: { src: string; alt: string }) {
  return (
    <div className="my-5 rounded-xl overflow-hidden border border-border shadow-sm bg-muted/20">
      {/* Fake browser chrome */}
      <div className="flex items-center gap-1.5 px-3 py-2.5 bg-muted/60 border-b border-border">
        <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-yellow-400/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-green-400/70" />
        <span className="ml-2 flex-1 bg-background/60 rounded text-[10px] text-muted-foreground px-2 py-0.5 max-w-[260px]">
          commerceiq.up.railway.app
        </span>
      </div>
      <img
        src={src}
        alt={alt}
        className="w-full h-auto block"
        loading="lazy"
      />
    </div>
  );
}

/* Section */

function TutorialSection({ section, index }: { section: Section; index: number }) {
  const Icon = section.icon;
  return (
    <div id={section.id} className="scroll-mt-24">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary/10 flex-shrink-0">
          <Icon className="h-5 w-5 text-secondary" />
        </div>
        <div>
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Sección {index + 1}
          </span>
          <h2 className="text-xl font-bold text-foreground leading-tight">{section.title}</h2>
        </div>
      </div>
      <p className="text-muted-foreground mb-8 ml-[52px]">{section.subtitle}</p>

      <div className="ml-[52px] space-y-10">
        {section.steps.map((step, stepIdx) => (
          <div key={stepIdx} className="relative">
            {stepIdx < section.steps.length - 1 && (
              <div className="absolute left-[15px] top-[36px] bottom-[-32px] w-px bg-border" />
            )}

            <div className="flex gap-4">
              <div className="flex-shrink-0 flex h-8 w-8 items-center justify-center rounded-full bg-secondary text-secondary-foreground text-sm font-bold z-10">
                {stepIdx + 1}
              </div>

              <div className="flex-1 pb-2">
                <h3 className="font-semibold text-foreground mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{step.description}</p>

                {step.tip && (
                  <div className="flex gap-2 bg-secondary/5 border border-secondary/20 rounded-lg px-3 py-2.5 mt-3">
                    <Info className="h-4 w-4 text-secondary flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-secondary/90">{step.tip}</p>
                  </div>
                )}

                <Screenshot src={step.image} alt={step.imageAlt} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="border-t mt-10 mb-2" />
    </div>
  );
}

/* Main Page */

export function TutorialsPage() {
  const [activeSection, setActiveSection] = useState(SECTIONS[0].id);
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        }
      },
      { rootMargin: '-20% 0px -60% 0px' }
    );

    SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observerRef.current?.observe(el);
    });

    return () => observerRef.current?.disconnect();
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const totalSteps = SECTIONS.reduce((n, s) => n + s.steps.length, 0);

  return (
    <div className="py-12">
      <div className="container max-w-6xl">
        {/* Page header */}
        <div className="mb-10">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
            <BarChart3 className="h-4 w-4 text-secondary" />
            <span>CommerceIQ</span>
            <ChevronRight className="h-3 w-3" />
            <span>Guía de uso</span>
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-3">
            Guía completa de uso
          </h1>
          <p className="text-muted-foreground max-w-2xl text-base">
            Todo lo que necesitas para empezar a transformar tus datos de e-commerce en
            dashboards automáticos con KPIs e insights generados por IA.
          </p>

          <div className="flex items-center gap-5 mt-5">
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <CheckCircle2 className="h-4 w-4 text-success" />
              <span>{SECTIONS.length} secciones</span>
            </div>
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <ArrowRight className="h-4 w-4 text-secondary" />
              <span>{totalSteps} pasos</span>
            </div>
          </div>
        </div>

        {/* Layout: sidebar + content */}
        <div className="flex gap-10 items-start">

          {/* Sticky sidebar */}
          <aside className="hidden lg:block w-56 flex-shrink-0 sticky top-24">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-1">
              Contenido
            </p>
            <nav className="space-y-0.5">
              {SECTIONS.map((section) => {
                const Icon = section.icon;
                const isActive = activeSection === section.id;
                return (
                  <button
                    key={section.id}
                    onClick={() => scrollTo(section.id)}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-sm transition-colors ${
                      isActive
                        ? 'bg-secondary/10 text-secondary font-medium border-l-2 border-secondary pl-[10px]'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5 flex-shrink-0" />
                    <span className="leading-tight">{section.title}</span>
                  </button>
                );
              })}
            </nav>
          </aside>

          {/* Main content */}
          <main className="flex-1 min-w-0 space-y-4">
            {SECTIONS.map((section, idx) => (
              <TutorialSection key={section.id} section={section} index={idx} />
            ))}

            {/* Footer CTA */}
            <div className="bg-secondary/5 border border-secondary/20 rounded-xl p-6 mt-4 flex items-start gap-4">
              <div className="rounded-full bg-secondary/10 p-2.5 flex-shrink-0">
                <Sparkles className="h-5 w-5 text-secondary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground mb-1">¿Tienes alguna duda?</h3>
                <p className="text-sm text-muted-foreground">
                  Consulta la sección de{' '}
                  <a href="/faq" className="text-secondary hover:underline font-medium">
                    Preguntas frecuentes
                  </a>{' '}
                  o escríbenos directamente desde{' '}
                  <a href="/contact" className="text-secondary hover:underline font-medium">
                    Contacto
                  </a>
                  .
                </p>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}