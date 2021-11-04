from Choice_Coin_Voting import create_app, db

app = create_app()


@app.before_first_request
def create_db_tables():
    db.create_all()

if __name__=="__main__":
    app.run(debug=True)