from Security.BaseModels import ChatMessage

def save_user_message(db, chat_id, content, image=None):
    msg = ChatMessage(
        chat_id=chat_id,
        sender="user",
        content=content,
        image=image
    )
    db.add(msg)
    db.commit()

def save_assistant_message(db, chat_id, content):
    msg = ChatMessage(
        chat_id=chat_id,
        sender="assistant",
        content=content
    )
    db.add(msg)
    db.commit()

def get_chat_history(db, chat_id):
    return db.query(ChatMessage).filter(
        ChatMessage.chat_id == chat_id
    ).order_by(ChatMessage.created_at.asc()).all()
