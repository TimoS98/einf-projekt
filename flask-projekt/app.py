from flask import Flask, render_template,request,redirect,url_for,jsonify,session;
import sqlite3

app = Flask(__name__)
app.secret_key = "secret"
# speichern einer neuen Liste in der DB 
@app.route("/save_list",methods=["GET","POST"])
def saveList():
 
 data = request.get_json()
 list_name = data["listname"]
 
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

 

 return jsonify({"listID":last_list_insert, "listenname":list_name})

# Initliasierung der DB
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
# Abfragen von Logindaten aus der DB 
@app.route("/", methods=["GET", "POST"])
def home():
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
      
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
 
# Neu registrieren in der Anwendung und Nutzerdaten speichern in DB 
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
# öffnen einer Liste und dazugehörige Einträge laden 
@app.route("/open_list",methods=["POST","GET"])
def open_list():
   if "user_id" in session: #abfangen von wieder in die liste kommen nach loggout(geht nicht. zurückknopf keine neue request)
    data = request.get_json()
    session["list_id"] = data["listenid"]  
    return jsonify({"status":"ok"}) 


# öffnen einer Liste 
@app.route("/open_list_page",methods=["POST","GET"])
def open_list_page():
   
   listen_id = session["list_id"]
   conn = sqlite3.connect("todo.db")
   conn.row_factory = sqlite3.Row
   cursor = conn.cursor()
   
   cursor.execute("""
         SELECT Name, Prioritaet From todo WHERE ListenID = ?       
    """,(listen_id,))
   
   todos = cursor.fetchall()

   conn.close()
   
  
   return  render_template("listen_einsicht.html", todos=todos)

#laden aller Listen des angemeldeten Users 
@app.route("/listen.html",methods=["POST","GET"])
def lists():
   if request.method=="GET":
      conn = sqlite3.connect("todo.db")
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor()

      cursor.execute("""SELECT Listen.ListenID, Listen.Listenname 
                        FROM userLists, Listen
                        WHERE userLists.UserID = ?
                        AND userLists.ListenID = Listen.ListenID"""
                     ,(session["user_id"],))
      listen = cursor.fetchall()
      conn.close()
      return jsonify([dict(liste) for liste in listen])

# logout des Users und löschen der Session   
@app.route("/logout",methods=["POST","GET"])
def logout(): 
    if request.method == "GET":
       session.clear() 
       
       return render_template("login.html")
#Prüfung, ob der User angemeldet ist    
@app.route("/backward",methods=["POST","GET"])
def backward():
   if "user_id" in session:
      return render_template("listen.html")
   return render_template("login.html")

# Verknüpfen eines Users mit einer Liste 
@app.route("/add_list_with_id",methods=["GET","POST"])
def add_list_with_id():
   
   data = request.get_json()
   listen_id = data["listenid"]
   conn = sqlite3.connect("todo.db")
   conn.row_factory = sqlite3.Row
   cursor = conn.cursor()
   vorhanden = cursor.execute("""
                         SELECT * FROM userLists  WHERE  ListenID = ? AND UserID = ?
                              """,(listen_id,session["user_id"])).fetchone()
   
   if vorhanden is  None: 
    cursor.execute("""
        INSERT INTO userLists (UserID, ListenID)
        VALUES (?,?)
    """,(session["user_id"],listen_id,))
    conn.commit()
    neue_Liste = cursor.execute("""
        SELECT Listenname, ListenID
        FROM Listen
        WHERE ListenID = ?
    """,(listen_id,)).fetchone()
    
    conn.close()
    return jsonify([dict(neue_Liste)]) 
   else: 
       return jsonify({"error": "Liste existiert schon"}), 404
      

# laden einer Liste 
@app.route("/load_list",methods=["GET","POST"])
def load_list():
   data = request.get_json()
   listen_id = data["listenid"]
   conn = sqlite3.connect("todo.db")
   conn.row_factory = sqlite3.Row
   cursor = conn.cursor()
   liste = cursor.execute("""
        SELECT ListenID,Listenname FROM Listen WHERE ListenID = ?
""",(listen_id,)).fetchone()
   conn.close()
   return [dict(liste)]
# User zu einer Liste mittels email und ListenID hinzufügen 
@app.route("/add_user",methods=["GET","POST"])
def add_user():
   if "user_id" in session:
      data = request.get_json()
      user_email = data["email"]
      list_id = data["listenid"]
      conn = sqlite3.connect("todo.db")
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor()
      user_exists = cursor.execute("""
        SELECT * FROM users WHERE email = ?
        """,(user_email,)).fetchone() 
      if user_exists is None:
       conn.close()
       return jsonify({"error": "User existiert nicht"}), 404
      list_exist = cursor.execute("""
        SELECT * FROM Listen WHERE ListenID = ?
        """,(list_id,)).fetchone() 
      if list_exist is None:
       conn.close()
       return jsonify({"error": "Liste existiert nicht"}), 404
      else:
       cursor.execute("""INSERT INTO userLists (UserID,ListenID) VALUES(?,?)""",(user_exists["UserID"],list_id))
       conn.commit()
       conn.close()
       return jsonify({"status": "ok"})
   else: 
       return jsonify({"error": "Nicht eingeloggt"}), 403

# löschen einer Liste aus der DB 
@app.route("/delete_list",methods=["GET","POST"])
def delete_liste():
    if "user_id" in session:
        data = request.get_json()
        list_id = data["listenid"]
        conn = sqlite3.connect("todo.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(""" 
               DELETE FROM userLists WHERE userID = ? AND ListenID = ?         
        """,(session["user_id"],list_id))
        conn.commit()
        listen = cursor.execute(""" 
                SELECT * FROM userLists WHERE   ListenID = ?      
                       """,(list_id,)).fetchall()
        if not listen:
            cursor.execute("""
                           DELETE  FROM Listen WHERE ListenID = ?
                           """,(list_id,))
            conn.commit()
            cursor.execute("""
                           DELETE  FROM todo WHERE ListenID = ?
                           """,(list_id,))
            conn.commit()
            conn.close()
            return jsonify({"status": "Liste gelöscht"})
        conn.close()
        return jsonify({"status": "Liste gelöscht"})
# wechsel von register zu anmelden    
@app.route("/",methods=["GET"])
def anmelden_link():
   return render_template("login.html")
# laden einer Liste aus der DB 
@app.route("/take_list",methods=["GET","POST"])
def  take_list():
  if "user_id" in session:
    data = request.get_json()
    list_id = data["id"]
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
 
    list_content = cursor.execute("""
                SELECT * FROM todo WHERE ListenID = ?
                """,(list_id,)).fetchall()
    listenname = cursor.execute("""
                                SELECT Listenname FROM Listen WHERE ListenID = ?
                                """,(list_id,)).fetchone()
    
    if not list_content:
        conn.close()
        return jsonify({"error":"Die Liste existiert nicht"})
    
    
    
    conn.close()
    return jsonify({"listenname": listenname["Listenname"],"todos": [dict(entry) for entry in list_content]})
  return render_template("login.html")
# abspecpeichern der modifizierten Liste 
@app.route("/save_modified_list",methods=["POST","GET"])
def save_modified_list():
    data = request.get_json()
    list_name = data["listname"]
    
    id_list = data["id_list"]
    modified_todo_list = data["new_todo_list"]
    
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
             DELETE FROM todo WHERE ListenID = ?      
                   """,(id_list,))
    conn.commit()
    for elements in modified_todo_list:
        cursor.execute("""
                    INSERT INTO todo (ListenID, Prioritaet, Name)
            VALUES (?, ?, ?)
                       """,(id_list,elements["prio"],elements["name"]))
        conn.commit()
        
    cursor.execute("""
                   UPDATE Listen SET listenname = ? WHERE ListenID = ? 
                   """,(list_name,id_list,)) 
    conn.commit()
       
    conn.close()
       
    
    return jsonify({"listname":list_name})

init_db()  
if __name__ == "__main__":
    app.run(debug=True)
   
