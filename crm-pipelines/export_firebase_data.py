#!/usr/bin/env python3
"""
Export Firebase Firestore Data
First step: Export and analyze what data we have
"""

import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

def export_firebase_data():
    """Export all collections from Firestore"""
    
    # Initialize Firebase
    print("Initializing Firebase...")
    cred = credentials.Certificate('smart-money-education-e3565532c51b.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    # Get all collections
    print("\nFetching collections...")
    collections = db.collections()
    
    all_data = {}
    collection_stats = {}
    
    for collection in collections:
        collection_name = collection.id
        print(f"\nExporting collection: {collection_name}")
        
        # Get all documents
        docs = collection.stream()
        collection_data = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['_id'] = doc.id
            collection_data.append(doc_data)
        
        all_data[collection_name] = collection_data
        collection_stats[collection_name] = len(collection_data)
        
        print(f"  → Exported {len(collection_data)} documents")
        
        # Save each collection to separate file
        filename = f"firebase_export_{collection_name}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"  → Saved to {filename}")
    
    # Print summary
    print("\n" + "="*50)
    print("EXPORT SUMMARY")
    print("="*50)
    
    total_docs = 0
    for collection, count in collection_stats.items():
        print(f"{collection}: {count} documents")
        total_docs += count
    
    print(f"\nTotal documents: {total_docs}")
    print(f"Total collections: {len(collection_stats)}")
    
    # Save summary
    summary = {
        'export_date': datetime.now().isoformat(),
        'collections': collection_stats,
        'total_documents': total_docs,
        'total_collections': len(collection_stats)
    }
    
    with open('firebase_export_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\nExport complete! Check firebase_export_*.json files")
    
    return all_data, collection_stats

if __name__ == "__main__":
    try:
        data, stats = export_firebase_data()
        
        # Show sample data structure for each collection
        print("\n" + "="*50)
        print("SAMPLE DATA STRUCTURE")
        print("="*50)
        
        for collection_name, collection_data in data.items():
            if collection_data:
                print(f"\n{collection_name} - First document structure:")
                first_doc = collection_data[0]
                for key in first_doc.keys():
                    value_type = type(first_doc[key]).__name__
                    print(f"  - {key}: {value_type}")
                
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("1. The service account file 'smart-money-education-e3565532c51b.json' is in the current directory")
        print("2. You have proper permissions to access Firestore")
