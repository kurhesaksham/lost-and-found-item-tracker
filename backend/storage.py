import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

file_path = os.path.join(DATA_DIR, 'data/items.csv')

if not os.path.exists(file_path):
    df = pd.DataFrame({
        "id": [],
        "item_name": [],
        "description": [],
        "location_found_lost": [],
        "contact_info": [],
        "status": []
    })
    df.to_csv(file_path, index=False)


def load_csv(file_path):
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        return pd.DataFrame({
            "id": [],
            "item_name": [],
            "description": [],
            "location_found_lost": [],
            "contact_info": [],
            "status": []
        })
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame({
            "id": [],
            "item_name": [],
            "description": [],
            "location_found_lost": [],
            "contact_info": [],
            "status": []
        })


def export_df(df):
    try:
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        print(f"Failed while creating csv: {e}")
        return False


def save_item(data):
    try:
        df = load_csv(file_path)
        id_list = list(df["id"])
        if "id" not in data:
            for i in range(1, 1000):
                if i not in id_list:
                    data["id"] = i
                    break
            else:
                return False
        df = df._append(data, ignore_index=True)
        df['id'] = df["id"].astype("int64")
        export_df(df)
        return True
    except Exception as e:
        print(f"Failed while saving item: {e}")
        return False


def get_items():
    df = load_csv(file_path)
    expected_columns = ["id", "item_name", "description", "location_found_lost", "contact_info", "status"]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = None
    return df[expected_columns].to_dict(orient='records')


def update_item(data):
    try:
        df = load_csv(file_path)
        item_id = int(data["id"])
        indexed_row = df[df["id"] == item_id]
        if indexed_row.empty:
            return False, {}
        ind = indexed_row.index[0]
        for key, value in data.items():
            if key != "id":
                df.at[ind, key] = value
        export_df(df)
        return True, df.to_dict(orient='records')
    except Exception as e:
        print(f"Failed while updating item: {e}")
        return False, {}


def remove_item(item_id: int):
    try:
        df = load_csv(file_path)
        if item_id in list(df['id']):
            df = df[df['id'] != item_id]
            export_df(df)
            return True
        return False
    except Exception as e:
        print(f"Failed while deleting item: {e}")
        return False
