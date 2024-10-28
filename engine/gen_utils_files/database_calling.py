from pymongo import MongoClient,UpdateOne
import os
from bson import ObjectId

def user_item_helper(meta)-> dict:
    return{
        "userId":str(meta["_id"]),
        "name":(meta["name"]),
        "email":(meta["email"]),
        "organizationId":(meta["organizationId"]),
        "credits":(meta["credits"])
    } 
    
MONGODB_URL = os.environ['MONGODB_URL']
DATABASE_NAME = os.environ['DATABASE_NAME']

client = MongoClient(MONGODB_URL)

db = client.get_database(DATABASE_NAME)

userCollection = db.users

def updated_userDB_monogo(res: dict):
    
    userId_to_search = res['userId']
    update_scan_db = userCollection.update_one(
        {"_id": ObjectId(userId_to_search)},{
            "$set": {
                "credits":res['credits']
                # "studentInfo.studentNumber.number": res['studentInfo']['studentNumber']['number']
            }
            # upsert=True
        },
        upsert=True
    )
    
    if update_scan_db.acknowledged:
        return True
    else:
        return False
  
def get_user_metadata_from_mongo(user_id:str)->list:
    user_items = []
    for user_item in userCollection.find({"_id": ObjectId(user_id)}):
        user_items.append(user_item_helper(user_item))
    return user_items