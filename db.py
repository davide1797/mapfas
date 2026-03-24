import sqlite3

DB_PATH = "questions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sus_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL
    )
    """)

    cur.execute("DELETE FROM questions")

    cur.executemany("""
    INSERT INTO questions
        (question, option_a, option_b, option_c, option_d, correct_option)
        VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (
                "What does PFAS stand for?",
                "Polymer Fuel Analysis System",
                "Per- and Polyfluoroalkyl Substances",
                "Public Food Safety Act",
                "Protected Freshwater Areas System",
                "b"
            ),
            (
                "Which of the following properties makes PFAS particularly persistent in the environment?",
                "High solubility in water",
                "Strong carbon-fluorine bonds",
                "High volatility",
                "Rapid biodegradation",
                "b"
            ),
            (
                "Who is not in danger for the presence of PFAS?",
                "Plants",
                "Animals",
                "Rocks",
                "Humans",
                "c"
            ),
            (
                "What is one example of source of PFAS contamination near urban or industrial areas?",
                "Agricultural pesticides",
                "Food scraps",
                "Firefighting foams",
                "Natural decomposition",
                "c"
            ),
            (
                "Why are PFAS sometimes called \"forever chemicals\"?",
                "They resist breakdown in the environment for decades or centuries",
                "They cycle rapidly between air, water, and soil",
                "They evaporate immediately upon release",
                "They are naturally produced in large quantities",
                "a"
            ),
            (
                "Which chemical aspect influences the stability of PFAS in the environment?",
                "The interaction between carbon and fluorine atoms",
                "The amount of water they contact",
                "The temperature of the surrounding air",
                "The number of atoms of carbon",
                "d"
            ),
            (
                "Which of these is NOT a factor for a city for being affected by PFAS?",
                "The altitude of the city",
                "The presence of a company using PFAS nearby",
                "A river flowing through industrial areas",
                "The selling of PFAS-containing products",
                "a"
            ),
            (
                "What is the matrix of a measurement?",
                "The percentage of PFAS in a sample",
                "The type of environmental medium sampled (e.g., water, soil)",
                "The location where the sample was taken",
                "The type of PFAS measured",
                "b"
            ),
            (
                "What is the common unit measure of a measurement?",
                "kilograms",
                "liters",
                "meters",
                "grams per liter (g/L)",
                "d"
            ),
            (
                "What is an example of environment in which a PFAS CANNOT be measured?",
                "biota",
                "water",
                "lava",
                "air",
                "c"
            )
    ])

    cur.execute("DELETE FROM sus_questions")

    cur.executemany("""
    INSERT INTO sus_questions
        (question)
        VALUES (?)
        """, [
            ("I think that I would like to use this system frequently.",), ("I found the system unnecessarily complex.",), ("I thought the system was easy to use.",),
            ("I think that I would need the support of a technical person to be able to use this system.",), ("I found the various functions in this system were well integrated.",), 
            ("I thought there was too much inconsistency in this system.",), ("I would imagine that most people would learn to use this system very quickly.",), 
            ("I found the system very cumbersome to use.",), ("I felt very confident using the system.",), ("I needed to learn a lot of things before I could get going with this system.",)
    ])
    conn.commit()
    conn.close()

def get_question_by_order(order):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT question, option_a, option_b, option_c, option_d, correct_option
        FROM questions
        ORDER BY id
        LIMIT 1 OFFSET ?
    """, (order - 1,))

    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)

def get_sus_question_by_order(order):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT question
        FROM sus_questions
        ORDER BY id
        LIMIT 1 OFFSET ?
    """, (order - 1,))

    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)

def get_total_questions():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions")
    total = cur.fetchone()[0]
    conn.close()
    return total

def get_total_sus_questions():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sus_questions")
    total = cur.fetchone()[0]
    conn.close()
    return total