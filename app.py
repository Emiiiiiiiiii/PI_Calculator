from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)

TENSION_DISENO = 1000  # kg/cm²

def calcular_traccion_compresion(datos, subtipo):
    try:
        # Asegurarse de que los valores sean float o None
        datos['fuerza'] = float(datos['fuerza']) if datos['fuerza'] else None
        datos['diametro'] = float(datos['diametro']) if datos['diametro'] else None
        datos['ancho'] = float(datos['ancho']) if datos['ancho'] else None
        datos['alto'] = float(datos['alto']) if datos['alto'] else None
        
        if subtipo == 'tension':
            if datos['fuerza'] is None or (datos['ancho'] is None and datos['alto'] is None and datos['diametro'] is None):
                return "Error: Faltan datos. Se necesita fuerza y (ancho y alto) o diámetro."
            
            area = datos['ancho'] * datos['alto'] if datos['ancho'] and datos['alto'] else math.pi * (datos['diametro']/2)**2
            tension = datos['fuerza'] / area
            factor_seguridad = TENSION_DISENO / tension
            return f"La tensión es: {tension:.2f} kgF/cm². Factor de seguridad: {factor_seguridad:.2f}"
        
        elif subtipo == 'area':
            if datos['fuerza'] is None:
                return "Error: Faltan datos. Se necesita fuerza."
            
            area_min = datos['fuerza'] / TENSION_DISENO
            area_max = datos['fuerza'] / (TENSION_DISENO * 0.8)
            return f"Área mínima: {area_min:.2f} cm², Área máxima: {area_max:.2f}"
        
        elif subtipo == 'fuerza':
            if datos['ancho'] is None and datos['alto'] is None and datos['diametro'] is None:
                return "Error: Faltan datos. Se necesita (ancho y alto) o diámetro."
            
            area = datos['ancho'] * datos['alto'] if datos['ancho'] and datos['alto'] else math.pi * (datos['diametro']/2)**2
            fuerza = TENSION_DISENO * area
            return f"La fuerza que soporta es: {fuerza:.2f} kgF"
        
        elif subtipo == 'largo':
            area_min = datos['fuerza'] / TENSION_DISENO
            area_max = datos['fuerza'] / (TENSION_DISENO * 0.8)
            largo_min = math.sqrt(area_min)
            largo_max = math.sqrt(area_max)
            return f"Lado mínimo: {largo_min:.2f} cm, Lado máximo: {largo_max:.2f} cm"
        
        elif subtipo == 'diametro':
            area_min = datos['fuerza'] / TENSION_DISENO
            area_max = datos['fuerza'] / (TENSION_DISENO * 0.8)
            diametro_min = math.sqrt((4 * area_min) / math.pi)
            diametro_max = math.sqrt((4 * area_max) / math.pi)
            return f"Diámetro mínimo: {diametro_min:.2f} cm, Diámetro máximo: {diametro_max:.2f}"
        
        else:
            return f"Subtipo de cálculo no válido: {subtipo}"
    
    except Exception as e:
        return f"Error en el cálculo: {str(e)}"

def calcular_corte(datos, subtipo_corte):
    try:
        # Verificar que se haya proporcionado fuerza y al menos una dimensión
        if datos['fuerza'] is None:
            return "Error: Se necesita fuerza.", 400

        if datos['ancho'] is None and datos['alto'] is None and datos['diametro'] is None:
            return "Error: Faltan datos. Se necesita (ancho y alto) o diámetro.", 400

        # Obtener el coeficiente de forma
        coeficiente_forma = {
            'circular': 0.75,
            'anular': 0.5,
            'rectangular': 0.666
        }.get(datos['forma'], None)  # Obtener el coeficiente de forma según la forma

        if coeficiente_forma is None:
            return "Error: Forma no válida.", 400

        tension_corte = 1146

        # Calcular área
        if datos['diametro'] is not None:
            area = (math.pi * datos['diametro']**2) / 4
        elif datos['ancho'] is not None and datos['alto'] is not None:
            area = datos['ancho'] * datos['alto']
        else:
            area = (datos['fuerza']) / (tension_corte * coeficiente_forma)

        # Los subtipos
        if subtipo_corte == 'area':
            area_min = (datos['fuerza']) / (tension_corte * coeficiente_forma)
            area_max = (datos['fuerza']) / (tension_corte * coeficiente_forma * 0.8)
            return f"Área mínima: {area_min:.2f} cm², Área máxima: {area_max:.2f} cm²"

        elif subtipo_corte == 'fuerza':
            if datos['ancho'] is None and datos['alto'] is None and datos['diametro'] is None:
                return "Error: Faltan datos. Se necesita (ancho y alto) o diámetro.", 400
            fuerza = tension_corte * area * coeficiente_forma
            return f"La fuerza aplicada es: {fuerza:.2f} kgF"

        elif subtipo_corte == 'base':
            if datos['alto'] is None:
                return "Error: Se necesita altura para calcular la base.", 400
            base_min = datos['fuerza'] / (tension_corte * coeficiente_forma * datos['alto'])
            base_max = datos['fuerza'] / (tension_corte * coeficiente_forma * 0.8 * datos['alto'])
            return f"Base mínima: {base_min:.2f} cm, Base máxima: {base_max:.2f} cm"

        elif subtipo_corte == 'altura':
            if datos['ancho'] is None:
                return "Error: Se necesita ancho para calcular la altura.", 400
            altura_min = datos['fuerza'] / (tension_corte * coeficiente_forma * datos['ancho'])
            altura_max = datos['fuerza'] / (tension_corte * coeficiente_forma * 0.8 * datos['ancho'])
            return f"Altura mínima: {altura_min:.2f} cm, Altura máxima: {altura_max:.2f} cm"

        else:
            return f"Subtipo de cálculo no válido: {subtipo_corte}", 400

    except Exception as e:
        return f"Error en el cálculo: {str(e)}", 500

def calcular_flexion(datos):
    try:
        if datos['momento'] is None or datos['ancho'] is None or datos['alto'] is None:
            return "Error: Faltan datos. Se necesita momento, ancho y alto."
        
        momento_inercia = (datos['ancho'] * datos['alto']**3) / 12
        tension_flexion = (datos['momento'] * (datos['alto']/2)) / momento_inercia
        factor_seguridad = TENSION_DISENO / tension_flexion
        return f"La tensión de flexión máxima es: {tension_flexion:.2f} kgF/cm². Factor de seguridad: {factor_seguridad:.2f}"
    
    except Exception as e:
        return f"Error en el cálculo: {str(e)}"

def calcular_torsion(datos):
    try:
        if datos['momento'] is None or datos['diametro'] is None:
            return "Error: Faltan datos. Se necesita momento y diámetro."
        
        momento_polar = (math.pi * datos['diametro']**4) / 32
        tension_torsion = (datos['momento'] * (datos['diametro']/2)) / momento_polar
        factor_seguridad = TENSION_DISENO / tension_torsion
        return f"La tensión de torsión máxima es: {tension_torsion:.2f} kgF/cm². Factor de seguridad: {factor_seguridad:.2f}"
    
    except Exception as e:
        return f"Error en el cálculo: {str(e)}"

def calcular_pandeo(datos, subtipo_pandeo):
    try:
        if subtipo_pandeo == 'carga_critica':
            if datos['largo'] is None or datos['diametro'] is None:
                return "Error: Faltan datos. Se necesita largo y diámetro."

            # Fórmula de Euler para carga crítica de pandeo
            momento_inercia = (math.pi * datos['diametro']**4) / 64
            carga_critica = (math.pi**2 * TENSION_DISENO * momento_inercia) / (datos['largo']**2)
            return f"La carga crítica de pandeo es: {carga_critica:.2f} kgF"
        
        else:
            return f"Subtipo de cálculo no válido: {subtipo_pandeo}"
    
    except Exception as e:
        return f"Error en el cálculo: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        print("Datos recibidos:", request.form)
        datos = {k: float(v) if v and v.replace('.', '', 1).isdigit() else v for k, v in request.form.items()}
        
        tipo_calculo = datos.pop('tipo_calculo', None)
        subtipo_calculo = datos.pop('subtipo_calculo', None)

        # Definir la tensión de diseño según el tipo de cálculo
        if tipo_calculo == 'traccion_compresion':
            tension_diseno = 1000  # kg/cm²
        elif tipo_calculo == 'corte':
            tension_diseno = 864.72  # kg/cm²
        elif tipo_calculo == 'flexion':
            tension_diseno = 1488.79  # kg/cm²
        elif tipo_calculo == 'torsion':
            tension_diseno = 864.72  # kg/cm²
        elif tipo_calculo == 'pandeo':
            tension_diseno = 1000  # kg/cm² (puedes ajustar este valor según sea necesario)
        else:
            return jsonify({"resultado": f"Tipo de cálculo no válido: {tipo_calculo}"}), 400

        print(f"Tensión de diseño: {tension_diseno} kgF/cm²")
        
        # Actualizar la variable TENSION_DISENO
        global TENSION_DISENO
        TENSION_DISENO = tension_diseno

        print(f"Tipo de cálculo: {tipo_calculo}")
        print(f"Subtipo de cálculo: {subtipo_calculo}")
        print(f"Datos procesados: {datos}")

        if tipo_calculo == 'traccion_compresion':
            resultado = calcular_traccion_compresion(datos, subtipo_calculo)
        elif tipo_calculo == 'corte':
            subtipo_corte = datos.pop('subtipo_corte', None)
            resultado = calcular_corte(datos, subtipo_corte)
        elif tipo_calculo == 'flexion':
            resultado = calcular_flexion(datos)
        elif tipo_calculo == 'torsion':
            resultado = calcular_torsion(datos)
        elif tipo_calculo == 'pandeo':
            subtipo_pandeo = datos.pop('subtipo_pandeo', None)
            resultado = calcular_pandeo(datos, subtipo_pandeo)
        else:
            resultado = f"Tipo de cálculo no válido: {tipo_calculo}"

        print(f"Resultado: {resultado}")
        return jsonify({"resultado": resultado})

    except Exception as e:
        return jsonify({"resultado": f"Error en el cálculo: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)