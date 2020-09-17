import os
import csv
import psycopg2
from configparser import ConfigParser

base_dir = os.path.dirname(os.path.abspath(__file__))

# get database config
def database_config():
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read("{}/config.ini".format(base_dir))

    # get section, default to postgresql
    db = {}
    if parser.has_section("postgresql"):
        params = parser.items("postgresql")
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format("postgresql", "config.ini"))

    return db

def create_tables():
    """ create tables in the PostgreSQL database"""
    commands = (
        """
        DROP TABLE catalogues
        """,
        """
        DROP TABLE websites
        """,
        """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        SELECT uuid_generate_v1();
        """
        """
        CREATE TABLE catalogues (
            UID uuid DEFAULT uuid_generate_v1(),
            SiteName VARCHAR(100),
            SiteHomepage VARCHAR(100),
            ProductURL VARCHAR(255),
            ProductName VARCHAR(255),
            ProductDescription TEXT,
            ProductCategory VARCHAR(255),
            ProductBrand VARCHAR(255),
            UPC VARCHAR(50),
            upcCategory VARCHAR(255),
            upcBrand VARCHAR(100),
            upcSize VARCHAR(100),
            upcDimension VARCHAR(100),
            upcIngredients TEXT,
            bookmark BOOLEAN DEFAULT FALSE,
            excludeYN BOOLEAN DEFAULT FALSE,
            lastPrice FLOAT,
            currentPrice FLOAT,
            percentFromLastPrice FLOAT,
            datePriceChange date,
            dateCreated date,
            modifiedDate date default CURRENT_DATE,
            productImage VARCHAR(255),
            PRIMARY KEY (UID)
        )
        """,
        """
        CREATE TABLE websites (
            id SERIAL PRIMARY KEY,
            Company_Name VARCHAR(255),
            SiteName VARCHAR(255),
            RetailorBrand VARCHAR(50),
            Exclude VARCHAR(10),
            CategoryLookup TEXT,
            DescriptionLookup TEXT,
            Sign_Up_Deal VARCHAR(255),
            Sign_Up_Deal_ifYes VARCHAR(255),
            Shipping_Cost VARCHAR(255),
            IsShopify VARCHAR(255),
            IsMagento VARCHAR(255),
            IsOther VARCHAR(255),
            CrawlType VARCHAR(10),
            InventoryPath TEXT,
            DetailPattern VARCHAR(255),
            PaginationPattern VARCHAR(255),
            Redirect_URL VARCHAR(255)
        )
        """,
    )
    conn = None
    try:
        # read the connection parameters
        params = database_config()
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**params)

        # Setting auto commit false
        conn.autocommit = True

        # Creating a cursor object using the cursor() method
        cursor = conn.cursor()

        # create table one by one
        for command in commands:
            try:
                cursor.execute(command)
            except Exception as err:
                print(err)
                continue
        # close communication with the PostgreSQL database server
        cursor.close()
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def insert_websites():
    conn = None
    try:
        # read the connection parameters
        params = database_config()
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**params)

        # Setting auto commit false
        conn.autocommit = True

        # Creating a cursor object using the cursor() method
        cursor = conn.cursor()

        # load_websites
        with open('{}/websites.csv'.format(base_dir), 'r') as websites_csv:
            reader = csv.DictReader(websites_csv)

            for website in reader:
                insert_query = """ INSERT INTO websites (Company_Name, SiteName, RetailorBrand, Exclude, CategoryLookup, DescriptionLookup, Sign_Up_Deal, Sign_Up_Deal_ifYes, Shipping_Cost, IsShopify, IsMagento, IsOther, CrawlType, InventoryPath, DetailPattern, PaginationPattern, Redirect_URL) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                record_to_insert = ( website['Company_Name'], website['Website'], website['Site_catagory'], "No", "", "", website['Sign_Up_Deal'], website['Sign_Up_Deal_ifYes'], website['Shipping_Cost'], website['IsShopify'], website['IsMagento'], website['IsOther'], website['CrawlType'], website['InventoryPath'], website['DetailPattern'], website['PaginationPattern'], website['Redirect_URL'])
                cursor.execute(insert_query, record_to_insert)

        # close communication with the PostgreSQL database server
        cursor.close()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    create_tables()
    insert_websites()