from flask import Flask, render_template,request,redirect,url_for,jsonify,session;
import sqlite3

app = Flask(__name__)
app.secret_key = "secret"

@app.route("/save_list",methods=["GET","POST"])
def saveList():
 data = request.get_json()
 list_name = data["listname"]
 print(data)
 conn = sqlite3.connect("todo.db")
 cursor = conn.cursor()
 cursor.execute(
                """INSERT INTO Listen (Listenname) VALUES (?)""",
            (list_name,)
             )
 
 last_list_insert = cursor.lastrowid
 conn.commit()        
 conn.close()  

 conn = sqlite3.connect("todo.db")
 conn.execute("PRAGMA foreign_keys = ON")
 cursor = conn.cursor()
 listen = data["todos"]
 for item in listen: 
   prio = item["priority"] 
   titel = item["title"]
   cursor.execute("""
                INSERT INTO todo (ListenID, Prioritaet, Name)
            VALUES (?, ?, ?)
                """,(last_list_insert,prio,titel,))
   conn.commit()
 cursor.execute("""
                INSERT INTO userLists(UserID,ListenID) VALUES(?,?)
                """,(session["user_id"],last_list_insert))
 conn.commit()
 
 
 conn.close()

 

 return jsonify({"listID":last_list_insert})

def init_db():
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS todo (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        ListenID INTEGER,
        Prioritaet TEXT NOT NULL,
        Name TEXT NOT NULL,

        FOREIGN KEY (ListenID) REFERENCES Listen(ListenID)
    )
""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Listen (
        ListenID INTEGER PRIMARY KEY AUTOINCREMENT,
        Listenname TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
           CREATE TABLE IF NOT EXISTS users (
                   UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                   email TEXT NOT NULL UNIQUE,
                   firstname TEXT NOT NULL,
                   lastname TEXT NOT NULL,
                   password TEXT NOT NULL

                   )       
                   """)
    cursor.execute("""
              CREATE TABLE IF NOT EXISTS userLists(
                   UserID INTEGER ,
                   ListenID INTEGER,
                   FOREIGN KEY (ListenID) REFERENCES Listen(ListenID),
                   FOREIGN KEY (UserID) REFERENCES users(UserID)
        )   

    """)

    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
       # print("Username:", username)
       # print("Password:", password)
        conn = sqlite3.connect("todo.db")
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute("""
                   SELECT * FROM users WHERE email = ?    
            """,(username,))
        user = cursor.fetchone()
        if user == None: 
            conn.close()
            error = "Bitte erstellen Sie sich zuerst ein Konto"
            return render_template("login.html", error=error)
        if user["password"] != password:
            error = "Das Passwort ist falsch"
            return render_template("login.html", error=error)
             
        else: 
            session["user_id"] = user["UserID"] 
            session["email"] = user["email"]
            conn.close()
            return render_template("listen.html")
    elif request.method == "GET":
     return  render_template("login.html")



@app.route("/anmelden",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name= request.form["name"]
        lastname= request.form["nachname"]
        email =request.form["email"]
        passwort =request.form["passwort"]
        conn = sqlite3.connect("todo.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, firstname, lastname, password)
            VALUES (?, ?, ?, ?)
        """, (email, name, lastname, passwort))

        conn.commit()
        conn.close()
        return redirect(url_for("home"))
    
    return render_template("anmelden.html")
    
    

@app.route("/users")
def show_users():
    import sqlite3
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
   
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    conn.close()
    print(str([dict(user) for user in users]))
    return  str([dict(user) for user in users])

init_db()  
if __name__ == "__main__":
    app.run(debug=True)
   
