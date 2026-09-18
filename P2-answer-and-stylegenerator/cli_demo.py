import os
import warnings
warnings.filterwarnings('ignore')

from ragbot import RAGBot

def main():
    print("\n" + "="*60)
    print("🤖 Digital Media RAG Bot - Terminal Demo")
    print("="*60)
    print("Initializing bot, connecting to database...")
    
    bot = RAGBot()
    stats = bot.get_collection_stats()
    
    print(f"✅ Ready! Database contains {stats['total_chunks']} document chunks.")
    print("Type 'exit' or 'quit' to exit.")
    print("="*60)

    while True:
        query = input("\n👉 Your Question: ")
        
        if query.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
            
        if not query.strip():
            continue
            
        print("\n⏳ Thinking...\n")
        
        try:
            answer, ids, passages, metadatas = bot.ask(query)
            
            print(f"🤖 Bot Answer:\n{answer}")
            print("\n📚 Sources Used:")
            
            if passages and len(passages) > 0:
                for i, meta in enumerate(metadatas):
                    original_source = meta.get('source', '')
                    doc_name = meta.get('document_name', '')
                    
                    # Orijinal kaynak ismini goster
                    doc = original_source if original_source else doc_name
                    if original_source and doc_name and original_source != doc_name:
                        doc += f" (as {doc_name})"
                    if not doc:
                        doc = 'Unknown Document'
                    
                    # Tum detayli metadatalari topla
                    details = []
                    
                    # Egitim bilgileri
                    if meta.get('program'): details.append(f"Program: {meta['program']}")
                    if meta.get('degree'): details.append(f"Degree: {meta['degree']}")
                    if meta.get('year'): details.append(f"Year: {meta['year']}")
                    if meta.get('document_type'): details.append(f"Type: {meta['document_type']}")
                    
                    # Konum / Icerik bilgileri
                    if meta.get('page'): details.append(f"Page: {meta['page']}")
                    if meta.get('section_symbol'): details.append(f"Section: {meta['section_symbol']}")
                    
                    heading = meta.get('heading', meta.get('section_title', ''))
                    
                    print(f"  {i+1}. {doc}")
                    if details:
                        print(f"     [Tags: {', '.join(details)}]")
                    if heading:
                        print(f"     [Topic: {heading}]")
            else:
                print("  No matching sources found or unable to connect.")
        except Exception as e:
            print(f"An error occurred: {e}")
            
        print("\n" + "-" * 60)

if __name__ == "__main__":
    main()
