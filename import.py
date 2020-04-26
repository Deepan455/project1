import os,csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine =create_engine(os.getenv("DATABASE_URL"))
db=scoped_session(sessionmaker(bind=engine))

def main():
    engine.execute("CREATE TABLE users(id SERIAL PRIMARY KEY,name VARCHAR NOT NULL,email VARCHAR,username VARCHAR UNIQUE,password VARCHAR NOT NULL)")
    engine.execute("CREATE TABLE books(isbn VARCHAR PRIMARY KEY,title VARCHAR NOT NULL,author VARCHAR NOT NULL,year VARCHAR)")
    engine.execute("CREATE TABLE reviews(id SERIAL PRIMARY KEY,comment VARCHAR NOT NULL,rating DECIMAL(8,1),isbn VARCHAR NOT NULL,username VARCHAR NOT NULL)")
    k=open('books.csv')
    reader=csv.reader(k)
    for isbn,title,author,year in reader:
        if isbn != 'isbn':
            engine.execute("INSERT INTO books(isbn,title,author,year)VALUES(%s,%s,%s,%s)",(isbn,title,author,year))
    print("done")

    db.commit()

if __name__=="__main__":
    main()
