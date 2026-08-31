# -*- coding: utf-8 -*-
"""
Genera los modelos .alp de las pruebas de topes de AnyLogic PLE.

No construye modelos desde cero: parte de `MM1.alp` del TP 3, que ya se sabe que
compila y corre, y le cambia unicamente los parametros que cada prueba necesita.
Eso mantiene el riesgo en cero: si el modelo base abre, las variantes abren.

MM1.alp es Source -> Queue -> Delay -> Sink de Process Modeling Library.

OJO con el `delay`: en MM1 tiene CAPACIDAD 1, porque es el servidor unico del
M/M/1. Heredarlo sin tocar hace que la cola absorba todo y que solo un agente
este en servicio, lo que arruina las pruebas B y C. Las tres lo ponen en
capacidad infinita para que el delay se comporte como retardo puro.

Salida: anylogic/pruebas/*.alp  +  anylogic/pruebas/LEEME.md

Ver docs/pruebas-anylogic-topes.md para el protocolo y la tabla de resultados.
"""
import io
import os
import re
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(
    os.path.dirname(BASE),
    "TPs 2025 - Bruno Neirotti", "TP 3", "MM1.alp")
DESTINO = os.path.join(BASE, "anylogic", "pruebas")


# --------------------------------------------------------------------------
# Manipulacion del XML del .alp
# --------------------------------------------------------------------------

def _bloque(alp, nombre):
    """Devuelve (inicio, fin) del EmbeddedObject llamado `nombre`."""
    pat = (r'<EmbeddedObject>(?:(?!</EmbeddedObject>).)*?'
           r'<Name><!\[CDATA\[' + re.escape(nombre) + r'\]\]>'
           r'.*?</EmbeddedObject>')
    m = re.search(pat, alp, re.S)
    if not m:
        raise KeyError("no existe el bloque %r en el .alp" % nombre)
    return m.start(), m.end()


def set_param(alp, bloque, parametro, codigo, clase="CodeValue", unidad=None):
    """Fija el valor de un parametro de un bloque de biblioteca.

    Un parametro sin `<Value>` usa el default de la biblioteca; agregarselo es
    lo que lo convierte en un valor explicito. Esa es toda la mecanica.
    """
    ini, fin = _bloque(alp, bloque)
    cuerpo = alp[ini:fin]

    if unidad is not None:
        valor = ('<Value Class="%s"><Code><![CDATA[%s]]></Code>'
                 '<Unit Class="TimeUnits"><![CDATA[%s]]></Unit></Value>'
                 % (clase, codigo, unidad))
    else:
        valor = ('<Value Class="%s"><Code><![CDATA[%s]]></Code></Value>'
                 % (clase, codigo))

    # con valor previo -> reemplazar; sin valor previo -> insertar
    con_valor = (r'(<Parameter>\s*<Name><!\[CDATA\[' + re.escape(parametro) +
                 r'\]\]></Name>\s*)<Value\b.*?</Value>')
    nuevo, n = re.subn(con_valor, lambda m: m.group(1) + valor, cuerpo, count=1, flags=re.S)

    if n == 0:
        vacio = (r'(<Parameter>\s*<Name><!\[CDATA\[' + re.escape(parametro) +
                 r'\]\]></Name>\s*)(</Parameter>)')
        nuevo, n = re.subn(vacio, lambda m: m.group(1) + valor + m.group(2),
                           cuerpo, count=1, flags=re.S)

    if n == 0:
        raise KeyError("el bloque %r no tiene el parametro %r" % (bloque, parametro))

    return alp[:ini] + nuevo + alp[fin:]


def set_tiempo_final(alp, segundos):
    """Fija FinalTime en el RunConfiguration y en todos los experimentos."""
    return re.sub(r'<FinalTime><!\[CDATA\[[^\]]*\]\]></FinalTime>',
                  '<FinalTime><![CDATA[%.1f]]></FinalTime>' % segundos, alp)


def set_modo_ejecucion(alp, modo="virtualTime"):
    return re.sub(r'<ExecutionMode>[^<]*</ExecutionMode>',
                  '<ExecutionMode>%s</ExecutionMode>' % modo, alp)


def set_memoria(alp, mb):
    return re.sub(r'<MaximumMemory>\d+</MaximumMemory>',
                  '<MaximumMemory>%d</MaximumMemory>' % mb, alp)


def renombrar(alp, nombre, paquete):
    """Renombra el modelo y su paquete Java.

    OJO: no alcanza con cambiar `JavaPackageName`. Los `<Connector>` referencian
    los bloques por (PackageName, ClassName, ItemName), y su PackageName es el
    paquete del modelo. Si se renombra el paquete sin actualizar esas
    referencias, AnyLogic no resuelve el EmbeddedObject y falla al construir con

        NullPointerException: Cannot invoke
        "OMEmbeddedObject.isReplicatedFlag()" because "<parameter1>" is null

    y los bloques aparecen sueltos, sin conectores. Verificado el 25/08/2026.
    """
    m = re.search(r'<JavaPackageName><!\[CDATA\[([^\]]*)\]\]></JavaPackageName>', alp)
    if not m:
        raise KeyError("el .alp no declara JavaPackageName")
    anterior = m.group(1)

    alp = re.sub(r'(<Model>\s*<Id>\d+</Id>\s*<Name><!\[CDATA\[)[^\]]*(\]\]>)',
                 lambda mm: mm.group(1) + nombre + mm.group(2), alp, count=1)
    alp = re.sub(r'<JavaPackageName><!\[CDATA\[[^\]]*\]\]></JavaPackageName>',
                 '<JavaPackageName><![CDATA[%s]]></JavaPackageName>' % paquete,
                 alp, count=1)

    # todas las referencias cruzadas al paquete anterior
    alp = alp.replace('<PackageName><![CDATA[%s]]></PackageName>' % anterior,
                      '<PackageName><![CDATA[%s]]></PackageName>' % paquete)
    return alp


# --------------------------------------------------------------------------
# Las tres pruebas
# --------------------------------------------------------------------------

def prueba_a(alp):
    """A - ¿Process Modeling Library corre mas de 5 h de tiempo simulado?

    Pocas llegadas a proposito (~720 en 20 h) para que el tope de 50.000
    agentes no pueda contaminar el resultado. Lo unico que se mide es si el
    reloj del modelo llega a 72.000 s o se corta en 18.000 s.
    """
    alp = renombrar(alp, "PruebaA_PML_20h", "pruebaa")
    alp = set_param(alp, "source", "interarrivalTime", "exponential(0.01)",
                    clase="CodeUnitValue", unidad="SECOND")
    alp = set_param(alp, "delay", "delayTime", "exponential(0.1)",
                    clase="CodeUnitValue", unidad="SECOND")
    alp = set_param(alp, "queue", "maximumCapacity", "true")
    alp = set_param(alp, "delay", "maximumCapacity", "true")
    alp = set_tiempo_final(alp, 72000)      # 20 h
    return set_modo_ejecucion(alp)


def prueba_b(alp):
    """B - ¿El tope de 50.000 cuenta creaciones o entidades vivas?

    Una llegada por segundo y una demora media de 1 s: en todo momento hay
    ~1 agente vivo, pero el acumulado cruza 50.000 cerca de t=50.000 s.

    Si el modelo se detiene ahi, el tope cuenta CREACIONES, y entonces reciclar
    una poblacion en vez de crear y destruir es una salida real: baja el tamano
    de grupo k y sube la fidelidad visual.
    Si llega a 72.000 s, cuenta entidades VIVAS y reciclar no cambia nada.
    """
    alp = renombrar(alp, "PruebaB_Tope50k", "pruebab")
    alp = set_param(alp, "source", "interarrivalTime", "exponential(1)",
                    clase="CodeUnitValue", unidad="SECOND")
    alp = set_param(alp, "delay", "delayTime", "exponential(1)",
                    clase="CodeUnitValue", unidad="SECOND")
    alp = set_param(alp, "queue", "maximumCapacity", "true")
    alp = set_param(alp, "delay", "maximumCapacity", "true")
    alp = set_tiempo_final(alp, 72000)
    return set_modo_ejecucion(alp)


def prueba_c(alp):
    """C - ¿Cuanto tarda en reloj una corrida de 40.000 agentes y 19 h?

    Calibrada contra la escala real del TPI:
      - 40.014 agentes creados en 68.400 s, que es un dia de servicio
      - demora media de 2.000 s -> ~1.170 agentes vivos a la vez, que es el
        orden de los grupos simultaneos con k=25 en hora pico

    El tope de licencia no es el unico limite: si una corrida tarda demasiado,
    las diez replicaciones por escenario se vuelven impracticables.
    """
    alp = renombrar(alp, "PruebaC_Rendimiento", "pruebac")
    alp = set_param(alp, "source", "interarrivalTime", "exponential(0.585)",
                    clase="CodeUnitValue", unidad="SECOND")
    alp = set_param(alp, "delay", "delayTime", "triangular(600, 1800, 3600)",
                    clase="CodeUnitValue", unidad="SECOND")
    alp = set_param(alp, "queue", "maximumCapacity", "true")
    alp = set_param(alp, "delay", "maximumCapacity", "true")
    alp = set_tiempo_final(alp, 68400)      # 19 h
    alp = set_memoria(alp, 2048)
    return set_modo_ejecucion(alp)


def agregar_poblacion_declarada(alp, cantidad, nombre="poblacion", id_nuevo=1900000000001):
    """Agrega un EmbeddedObject replicado `cantidad` veces, sin conectores.

    Es el sustituto para preguntar si una poblacion DECLARADA cuenta contra el
    tope de 50.000. Los bloques de biblioteca son agentes: una replicacion de
    60.000 son 60.000 agentes, pero creados en la inicializacion y no
    dinamicamente por un Source.

    Se elige `Sink` porque no necesita parametros ni conexiones. Al no tener
    conectores, no toca la integridad referencial del flowchart existente.
    """
    bloque = """				<EmbeddedObject>
					<Id>%d</Id>
					<Name><![CDATA[%s]]></Name>
					<X>300</X><Y>400</Y>
					<Label><X>0</X><Y>-10</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<ActiveObjectClass>
						<PackageName><![CDATA[com.anylogic.libraries.processmodeling]]></PackageName>
						<ClassName><![CDATA[Sink]]></ClassName>
					</ActiveObjectClass>
					<Parameters>
					</Parameters>
					<ReplicationFlag>true</ReplicationFlag>
					<Replication Class="CodeValue">
						<Code><![CDATA[%d]]></Code>
					</Replication>
					<CollectionType>ARRAY_LIST_BASED</CollectionType>
					<InitialLocationType>XYZ</InitialLocationType>
					<ColumnCode Class="CodeValue"><Code><![CDATA[0]]></Code></ColumnCode>
					<RowCode Class="CodeValue"><Code><![CDATA[0]]></Code></RowCode>
					<LocationNameCode Class="CodeValue"><Code><![CDATA[""]]></Code></LocationNameCode>
					<InitializationType>SPECIFIED_NUMBER</InitializationType>
					<InitializationDatabaseType>ONE_AGENT_PER_DATABASE_RECORD</InitializationDatabaseType>
					<QuantityColumn>
					</QuantityColumn>
				</EmbeddedObject>
""" % (id_nuevo, nombre, cantidad)

    cierre = "			</EmbeddedObjects>"
    if cierre not in alp:
        raise KeyError("no se encuentra el cierre de <EmbeddedObjects>")
    return alp.replace(cierre, bloque + cierre, 1)


def prueba_d(alp):
    """D - ¿Una poblacion DECLARADA cuenta contra el tope de 50.000?

    La prueba B ya establecio que el tope cuenta CREACIONES: se corto en 50.027
    con un solo agente vivo. La pregunta que queda es si esas creaciones incluyen
    las poblaciones declaradas en la inicializacion o solo las dinamicas.

    Si NO cuentan, reciclar una poblacion en vez de crear y destruir permite
    bajar mucho el tamano de grupo k, con dos efectos: mas figuras visibles y
    menos cuantizacion en el indicador de no-abordaje.

    El modelo lleva 60.000 bloques Sink replicados, sin conectar, mas el
    flowchart de siempre con llegadas ralas.
    """
    alp = renombrar(alp, "PruebaD_PoblacionDeclarada", "pruebad")
    alp = set_param(alp, "source", "interarrivalTime", "exponential(0.01)",
                    clase="CodeUnitValue", unidad="SECOND")
    alp = set_param(alp, "delay", "delayTime", "exponential(0.1)",
                    clase="CodeUnitValue", unidad="SECOND")
    alp = set_param(alp, "queue", "maximumCapacity", "true")
    alp = set_param(alp, "delay", "maximumCapacity", "true")
    alp = agregar_poblacion_declarada(alp, 60000)
    alp = set_tiempo_final(alp, 3600)       # 1 h: no interesa el reloj
    alp = set_memoria(alp, 2048)
    return set_modo_ejecucion(alp)


def prueba_e(alp):
    """E - ¿Cuanta memoria cuesta el pool que el modelo realmente necesita?

    La prueba D establecio que una poblacion DECLARADA no cuenta contra el tope
    de 50.000, pero su Replicas10 murio con OutOfMemoryError: 60.000 bloques con
    animacion no entran en 2 GB. El limite se mudo de la licencia a la memoria.

    Y 60.000 era muy por encima de lo necesario. Por la ley de Little, con la
    demanda real del TPI y una permanencia media de 1.030 s, la CONCURRENCIA en
    hora pico a k=1 es de **20.722 pasajeros vivos a la vez**. Lo que rompe el
    tope no es la concurrencia sino el acumulado del dia, 740.568 creaciones.

    Por eso esta prueba usa **25.000**, que cubre el pico a k=1 con margen, y
    sube la memoria a 4 GB. El bloque Sink es MAS PESADO que un agente propio
    minimo, asi que el resultado es conservador: si 25.000 Sink entran, un
    Pasajero liviano entra con holgura.
    """
    alp = renombrar(alp, "PruebaE_PoolRealista", "pruebae")
    alp = set_param(alp, "source", "interarrivalTime", "exponential(0.01)",
                    clase="CodeUnitValue", unidad="SECOND")
    alp = set_param(alp, "delay", "delayTime", "exponential(0.1)",
                    clase="CodeUnitValue", unidad="SECOND")
    alp = set_param(alp, "queue", "maximumCapacity", "true")
    alp = set_param(alp, "delay", "maximumCapacity", "true")
    alp = agregar_poblacion_declarada(alp, 25000, id_nuevo=1900000000002)
    alp = set_tiempo_final(alp, 3600)
    alp = set_memoria(alp, 4096)
    return set_modo_ejecucion(alp)


PRUEBAS = [
    ("PruebaA_PML_20h.alp", prueba_a),
    ("PruebaB_Tope50k.alp", prueba_b),
    ("PruebaC_Rendimiento.alp", prueba_c),
    ("PruebaD_PoblacionDeclarada.alp", prueba_d),
    ("PruebaE_PoolRealista.alp", prueba_e),
]


def main():
    if not os.path.exists(ORIGEN):
        raise SystemExit("no se encuentra el modelo base: %s" % ORIGEN)

    if not os.path.isdir(DESTINO):
        os.makedirs(DESTINO)

    base = io.open(ORIGEN, encoding="utf-8").read()
    print("modelo base: %s (%d bytes)" % (os.path.basename(ORIGEN), len(base)))

    for nombre, fn in PRUEBAS:
        alp = fn(base)
        ruta = os.path.join(DESTINO, nombre)
        io.open(ruta, "w", encoding="utf-8", newline="\n").write(alp)

        # control 1: que siga siendo XML bien formado
        import xml.etree.ElementTree as ET
        ET.parse(ruta)

        # control 2: integridad referencial de los conectores.
        # Cada <Connector> apunta a bloques por (PackageName, ClassName,
        # ItemName). Si alguna referencia nombra un paquete que ya no existe,
        # AnyLogic construye null y revienta. Esto lo detecta antes de abrirlo.
        paquete = re.search(r'<JavaPackageName><!\[CDATA\[([^\]]*)\]\]>', alp).group(1)
        bloques = set(re.findall(
            r'<EmbeddedObject>(?:(?!</EmbeddedObject>).)*?<Name><!\[CDATA\[([^\]]+)\]\]>',
            alp, re.S))
        rotas = []
        for c in re.finditer(r'<Connector>.*?</Connector>', alp, re.S):
            for ref in re.finditer(
                    r'<(?:Source|Target)EmbeddedObjectReference>\s*'
                    r'<PackageName><!\[CDATA\[([^\]]*)\]\]></PackageName>\s*'
                    r'<ClassName><!\[CDATA\[([^\]]*)\]\]></ClassName>\s*'
                    r'<ItemName><!\[CDATA\[([^\]]*)\]\]></ItemName>',
                    c.group(0), re.S):
                pkg, _, item = ref.groups()
                if pkg != paquete or item not in bloques:
                    rotas.append((pkg, item))
        if rotas:
            raise AssertionError(
                "%s: referencias de conector rotas -> %s" % (nombre, rotas))

        n_conn = len(re.findall(r'<Connector>', alp))
        print("  %-28s %7d bytes  XML valido  %d conectores OK"
              % (nombre, len(alp), n_conn))

    print("\nsalida en: %s" % DESTINO)


if __name__ == "__main__":
    main()
