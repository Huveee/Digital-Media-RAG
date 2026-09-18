from Security.userdatabase import engine
from Security.dbBase import Base

# Import ALL MODELS before create_all!
from Security.BaseModels import UserModel, ChatModel, ChatMessage

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
