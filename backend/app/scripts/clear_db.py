import os

from dotenv import load_dotenv
from pymongo import MongoClient


def clear_collections_except_users(env_path):
    print(f"Loading environment variables from: {env_path}")

    # 1. Load the .env file from the provided path
    load_dotenv(dotenv_path=env_path)

    # 2. Retrieve the updated variables from your .env
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")

    if not mongo_uri:
        raise ValueError("MONGODB_URI is missing from the .env file.")
    if not db_name:
        raise ValueError(
            "MONGODB_DB_NAME is empty or missing from the .env file. Please specify your database name in the .env file."
        )

    try:
        # 3. Connect to MongoDB
        client = MongoClient(mongo_uri)

        # Select the database explicitly using your db_name variable
        db = client[db_name]
        print(f"Connected to database: {db.name}")

        # 4. Get all collection names in the database
        collections = db.list_collection_names()

        if not collections:
            print("No collections found in the database.")
            return

        # 5. Iterate and delete documents
        for coll_name in collections:
            if coll_name.lower() == "users":
                print("Skipping collection: 'users'")
                continue

            result = db[coll_name].delete_many({})
            print(f"Cleared '{coll_name}': deleted {result.deleted_count} documents.")

        print("\nCleanup successfully completed.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Always close the connection when done
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    # Dynamically calculate the path to the .env file
    # This works as long as the script is in app/scripts/ and .env is in the root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    env_file_path = os.path.join(root_dir, ".env")

    # Run the function
    clear_collections_except_users(env_file_path)
