from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from rdflib import Graph
import sqlite3
from flask import send_file
import os
from db import init_db
from db import get_question_by_order
from db import get_sus_question_by_order
from db import get_total_questions
from db import get_total_sus_questions
from flask import session
from flask import Flask, Response, render_template

app = Flask(__name__)
app.secret_key = "secret_session"

BASE_DIR = "/home/depierro/Desktop/INRAe/Semantics 2026/mapfas"
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "download")  
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

file_ontology = "pfas.rdf"
ontology_path = os.path.join(DOWNLOAD_FOLDER, file_ontology)

g = Graph()
g.parse(ontology_path, format="xml")
init_db()
DB_TABLE = "questions.db"

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        return redirect(url_for("map_view"))

    return render_template("home.html")

@app.route("/download", methods=["GET", "POST"])
def download_file():
    return send_file(
        ontology_path,
        as_attachment=True,
        download_name="pfas_ontology.rdf"
    )

@app.route("/upload", methods=["POST"])
def upload_file():
    uploaded_file = request.files.get("ontology_file")
    if uploaded_file:
        uploaded_path = os.path.join(DOWNLOAD_FOLDER, "custom_pfas.rdf")
        uploaded_file.save(uploaded_path)
        g.remove((None, None, None))
        g.parse(uploaded_path, format="xml")
        return redirect(url_for("map_view"))
    return "No file uploaded.", 400

@app.route("/map_view")
def map_view():
    return render_template("map.html")

@app.route("/map_view_svg")
def map_view_svg():
    base_image_url = "/static/maps/map.svg"  
    width, height = 3200, 2400

    q = f"""
    PREFIX ontopfas: <https://w3id.org/OntoPFAS#>
    PREFIX geo: <https://www.w3.org/2003/01/geo/wgs84_pos#>

    SELECT ?measurement ?cx ?cy 
        WHERE {{
        ?measurement ontopfas:measuredIn ?city .
        ?city geo:long ?cx  ;
            geo:lat ?cy .
        }}
    """
    circles = []
    for row in g.query(q):
        measurement = row.measurement.split("#")[-1]
        cx = float(row.cx)
        cy = float(row.cy)

        circles.append({"data-place": measurement, "cx": cx, "cy": cy})

    # Start SVG
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    
    # Add base image
    svg += f'<image href="{base_image_url}" width="{width}" height="{height}" />'

    # Add circles dynamically
    svg += '<g id="markers">'
    for c in circles:
        svg += f'<circle data-place="{c["data-place"]}" class="map-point expandable" fill="orange" r="40" cx="{c["cx"]}" cy="{c["cy"]}" style="cursor:pointer"/>'
    svg += '</g>'
    svg += '</svg>'

    return Response(svg, mimetype='image/svg+xml')

def get_questions():
    conn = sqlite3.connect(DB_TABLE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM questions ORDER BY order")
    rows = cur.fetchall()
    conn.close()

    questions_dict = {}

    for row in rows:
        order = row[0]  # or use enumerate if you prefer
        questions_dict[order] = {
            "question": row[1],
            "option_a": row[2],
            "option_b": row[3],
            "option_c": row[4],
            "option_d": row[5],
            "correct_option": row[6]
        }

    return questions_dict

@app.route("/test", methods=["GET", "POST"])
def test():
    total = get_total_questions()

    if request.method == "POST":
        if "order" not in session:
            session["order"] = 1
            session["score"] = 0

        selected = request.form.get("answer")
        correct = request.form.get("correct")
        session["result"] = "Incorrect"
        if selected == correct:
            session["score"] += 1
            session["result"] = "Correct"

        session["order"] += 1

        return redirect(url_for("test"))

    if "order" not in session:
        session["order"] = 1
        session["score"] = 0
        session["result"] = None

    result = session.pop("result", None)

    if session["order"] > total:
        final_score = session["score"]
        last_question = get_question_by_order(total)
        session.clear()

        return render_template(
            "test.html",
            question=last_question,
            finished=True,
            result=result,
            score=final_score,
            total=total
        )

    question = get_question_by_order(session["order"])

    return render_template(
        "test.html",
        question=question,
        result=result,
        finished=False
    )

@app.route("/questionnaire", methods=["GET", "POST"])
def questionnaire():
    total = get_total_sus_questions()

    if request.method == "POST":
        selected = request.form.get("answer")
        if session["order"] % 2 == 1:
            session["score"] += int(selected)
        else:
            session["score"] += (4 - int(selected))

        session["order"] += 1
        return redirect(url_for("questionnaire"))

    if "order" not in session:
        session["order"] = 1
        session["score"] = 0

    if session["order"] > total:
        final_score = session["score"] * 2.5
        last_question = get_sus_question_by_order(total)
        session.clear()

        return render_template(
            "questionnaire.html",
            question=last_question,
            finished=True,
            score=final_score,
            total=total
        )

    question = get_sus_question_by_order(session["order"])

    return render_template(
        "questionnaire.html",
        question=question,
        finished=False
    )

@app.route("/location/measurement/<measurement>")
def get_measurement(measurement):
    q = f"""
    PREFIX ontopfas: <https://w3id.org/OntoPFAS#>
    PREFIX sosa: <http://www.w3.org/ns/sosa/>

    SELECT ?city ?quantity 
    WHERE {{
    # Get measurement city and quantity
    ontopfas:{measurement} ontopfas:measuredIn ?city ;
                           sosa:hasSimpleResult ?quantity .
    }}
    """
    results = []
    for row in g.query(q):
        city = row.city.split("#")[-1]
        quantity = float(row.quantity)
        results.append({
            "city": city,
            "quantity": quantity,
            "description": f"In the nearby of {city}, a measurement of {quantity} ng/L of PFAS has been sampled."
        })
    return jsonify(results)
    
@app.route("/location/company/<company>")
def get_company(company):
    results = []
    results.append({
        "company": company
    })
    return jsonify(results)

@app.route("/nearby_companies/<measurement>")
def nearby_companies(measurement):  
    q = f"""
    PREFIX ontopfas: <https://w3id.org/OntoPFAS#>
    PREFIX geo: <https://www.w3.org/2003/01/geo/wgs84_pos#>
    PREFIX schema: <https://schema.org/>

    SELECT ?activity ?cx ?cy ?mLat ?mLon
    WHERE {{
    # Get measurement place coordinates
    ontopfas:{measurement} ontopfas:measuredIn ?place .
    ?place geo:lat ?mLat ;
           geo:long ?mLon . 

    ?activity a schema:Organization ;
        geo:long ?cx ;
        geo:lat ?cy .
    
    # Simple Euclidean distance filter
    FILTER( ( (?cx - ?mLon)*(?cx - ?mLon) + (?cy - ?mLat)*(?cy - ?mLat) ) < 80000 )
    }}
    """
    results = []
    for row in g.query(q):
        results.append({
            "id": row.activity.split("#")[-1],
            "cx": float(row.cx),
            "cy": float(row.cy)
        })
    return jsonify(results)

@app.route("/matrix/<measurement>")
def matrix(measurement):   

    q = f"""
    PREFIX ontopfas: <https://w3id.org/OntoPFAS#>

    SELECT ?matrix
    WHERE {{
    # Get matrix
    ontopfas:{measurement} ontopfas:matrix ?matrix .
    }}
    """

    results = []
    for row in g.query(q):
        results.append({
            "matrix": row.matrix.split("#")[-1]
        })
    return jsonify(results)

@app.route("/measured_pfas/<measurement>")
def measured_pfas(measurement):   

    q = f"""
    PREFIX ontopfas: <https://w3id.org/OntoPFAS#>

    SELECT ?pfas ?nCarbons
    WHERE {{
    # Get measured pfas
    ontopfas:{measurement} ontopfas:measuredPfas ?pfas .
    ?pfas ontopfas:numberOfCarbons ?nCarbons .
    }}
    """

    results = []
    for row in g.query(q):
        results.append({
            "pfas": row.pfas.split("#")[-1],
            "nCarbons": int(row.nCarbons)
        })
    return jsonify(results)

@app.route("/affected_cities/<measurement>")
def affected_cities(measurement):   
    q = f"""
    PREFIX ontopfas: <https://w3id.org/OntoPFAS#>
    PREFIX geo: <https://www.w3.org/2003/01/geo/wgs84_pos#>
    PREFIX schema: <https://schema.org/>
    PREFIX obo: <http://purl.obolibrary.org/obo/>

    SELECT ?nearCity ?cx ?cy (MIN(?conn) AS ?connection)
    WHERE {{
        ontopfas:{measurement} ontopfas:measuredIn ?place .
        ?place geo:lat ?mLat ;
            geo:long ?mLon .

        ?city a schema:City ;
            geo:long ?cityX ;
            geo:lat ?cityY .

        FILTER( ( (?cityX - ?mLon)*(?cityX - ?mLon)
            + (?cityY - ?mLat)*(?cityY - ?mLat) ) < 80000 )

        ?city obo:RO_0002170* ?nearCity .
        ?nearCity geo:long ?cx ;
                geo:lat ?cy .

        OPTIONAL {{
            ?city obo:RO_0002170* ?nearCity2 .
            FILTER(?nearCity2 != ?city)
            BIND(?city AS ?conn)
        }}
    }}
    GROUP BY ?nearCity ?cx ?cy
    """
    results = []
    for row in g.query(q):
        results.append({
            "id": row.nearCity.split("#")[-1],
            "cx": float(row.cx),
            "cy": float(row.cy),
            "connection": row.connection.split("#")[-1] if row.connection else None
        })
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
